"""
Module description:

"""

__version__ = '0.3.0'
__author__ = 'Vito Walter Anelli, Claudio Pomo, Daniele Malitesta, Felice Antonio Merra'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it, daniele.malitesta@poliba.it, felice.merra@poliba.it'

from ast import literal_eval as make_tuple

from tqdm import tqdm
import numpy as np

from elliot.dataset.samplers import pointwise_pos_neg_ratio_ratings_sampler as ppnrrs
from elliot.recommender import BaseRecommenderModel
from elliot.recommender.base_recommender_model import init_charger
from elliot.recommender.recommender_utils_mixin import RecMixin
from .GCMCModel import GCMCModel


class GCMC(RecMixin, BaseRecommenderModel):
    r"""
    Graph Convolutional Matrix Completion

    For further details, please refer to the `paper <https://arxiv.org/abs/1706.02263>`_

    Args:
        lr: Learning rate
        epochs: Number of epochs
        factors: Number of latent factors
        batch_size: Batch size
        l_w: Regularization coefficient
        convolutional_layer_size: Tuple with number of units for each convolutional layer
        dense_layer_size: Tuple with number of units for each dense layer
        node_dropout: Tuple with dropout rate for each node
        dense_layer_dropout: Tuple with hidden layer dropout rate for each dense propagation layer

    To include the recommendation model, add it to the config file adopting the following pattern:

    .. code:: yaml

      models:
        GCMC:
          meta:
            save_recs: True
          lr: 0.0005
          epochs: 50
          batch_size: 512
          factors: 64
          l_w: 0.1
          convolutional_layer_size: (64,)
          dense_layer_size: (64,)
          node_dropout: ()
          dense_layer_dropout: (0.1,)
    """
    @init_charger
    def __init__(self, data, config, params, *args, **kwargs):

        self._sampler = ppnrrs.Sampler(self._data.i_train_dict, self._data.sp_i_train_ratings, 0)
        if self._batch_size < 1:
            self._batch_size = self._num_users

        ######################################

        self._params_list = [
            ("_learning_rate", "lr", "lr", 0.0005, None, None),
            ("_factors", "factors", "factors", 64, None, None),
            ("_l_w", "l_w", "l_w", 0.01, None, None),
            ("_convolutional_layer_size", "convolutional_layer_size", "convolutional_layer_size", "(64,)", lambda x: list(make_tuple(x)),
             lambda x: self._batch_remove(str(x), " []").replace(",", "-")),
            ("_dense_layer_size", "dense_layer_size", "dense_layer_size", "(64,)", lambda x: list(make_tuple(x)),
             lambda x: self._batch_remove(str(x), " []").replace(",", "-")),
            ("_node_dropout", "node_dropout", "node_dropout", "()", lambda x: list(make_tuple(x)),
             lambda x: self._batch_remove(str(x), " []").replace(",", "-")),
            ("_dense_layer_dropout", "dense_layer_dropout", "dense_layer_dropout", "()", lambda x: list(make_tuple(x)),
             lambda x: self._batch_remove(str(x), " []").replace(",", "-"))
        ]
        self.autoset_params()

        self._n_convolutional_layers = len(self._convolutional_layer_size)
        self._n_dense_layers = len(self._dense_layer_size)

        row, col = data.sp_i_train.nonzero()
        self.edge_index = np.array([row, col])

        self._model = GCMCModel(
            num_users=self._num_users,
            num_items=self._num_items,
            learning_rate=self._learning_rate,
            embed_k=self._factors,
            l_w=self._l_w,
            convolutional_layer_size=self._convolutional_layer_size,
            dense_layer_size=self._dense_layer_size,
            n_convolutional_layers=self._n_convolutional_layers,
            n_dense_layers=self._n_dense_layers,
            node_dropout=self._node_dropout,
            dense_layer_dropout=self._dense_layer_dropout,
            edge_index=self.edge_index,
            random_seed=self._seed
        )

    @property
    def name(self):
        return "GCMC" \
               + f"_{self.get_base_params_shortcut()}" \
               + f"_{self.get_params_shortcut()}"

    def train(self):
        if self._restore:
            return self.restore_weights()

        for it in self.iterate(self._epochs):
            loss = 0
            steps = 0
            with tqdm(total=int(self._data.transactions // self._batch_size), disable=not self._verbose) as t:
                for batch in self._sampler.step(self._data.transactions, self._batch_size):
                    steps += 1
                    loss += self._model.train_step(batch)
                    t.set_postfix({'loss': f'{loss / steps:.5f}'})
                    t.update()

            self.evaluate(it, loss / (it + 1))

    def get_recommendations(self, k: int = 100):
        predictions_top_k_test = {}
        predictions_top_k_val = {}
        for index, offset in enumerate(range(0, self._num_users, self._batch_size)):
            offset_stop = min(offset + self._batch_size, self._num_users)
            predictions = self._model.predict(offset, offset_stop)
            recs_val, recs_test = self.process_protocol(k, predictions, offset, offset_stop)
            predictions_top_k_val.update(recs_val)
            predictions_top_k_test.update(recs_test)
        return predictions_top_k_val, predictions_top_k_test

    def get_single_recommendation(self, mask, k, predictions, offset, offset_stop):
        v, i = self._model.get_top_k(predictions, mask[offset: offset_stop], k=k)
        items_ratings_pair = [list(zip(map(self._data.private_items.get, u_list[0]), u_list[1]))
                              for u_list in list(zip(i.detach().cpu().numpy(), v.detach().cpu().numpy()))]
        return dict(zip(map(self._data.private_users.get, range(offset, offset_stop)), items_ratings_pair))
