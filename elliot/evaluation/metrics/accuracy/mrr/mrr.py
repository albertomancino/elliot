"""
This is the implementation of the MRR metric.
It proceeds from a user-wise computation, and average the values over the users.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import numpy as np
from evaluation.metrics.base_metric import BaseMetric


class MRR(BaseMetric):
    """
    This class represents the implementation of the MRR recommendation metric.
    Passing 'MRR' to the metrics list will enable the computation of the metric.
    """

    def __init__(self, recommendations, config, params, eval_objects):
        """
        Constructor
        :param recommendations: list of recommendations in the form {user: [(item1,value1),...]}
        :param cutoff: numerical threshold to limit the recommendation list
        :param relevant_items: list of relevant items (binary) per user in the form {user: [item1,...]}
        """
        super().__init__(recommendations, config, params, eval_objects)
        self._cutoff = self._evaluation_objects.cutoff
        self._relevant_items = self._evaluation_objects.relevance.get_binary_relevance()

    @staticmethod
    def name():
        """
        Metric Name Getter
        :return: returns the public name of the metric
        """
        return "MRR"

    @staticmethod
    def __user_mrr(user_recommendations, cutoff, user_relevant_items):
        """
        Per User Precision
        :param user_recommendations: list of user recommendation in the form [(item1,value1),...]
        :param cutoff: numerical threshold to limit the recommendation list
        :param user_relevant_items: list of user relevant items in the form [item1,...]
        :return: the value of the Precision metric for the specific user
        """
        return MRR.__get_reciprocal_rank(user_recommendations[:cutoff], user_relevant_items)

    @staticmethod
    def __get_reciprocal_rank(user_recommendations, user_relevant_items):
        for r, (i, v) in enumerate(user_recommendations):
            if i in user_relevant_items:
                return 1 / (r + 1)
        return 0

    def eval(self):
        """
        Evaluation function
        :return: the overall averaged value of Precision
        """
        return np.average(
            [MRR.__user_mrr(u_r, self._cutoff, self._relevant_items[u])
             for u, u_r in self._recommendations.items()]
        )

    def eval_user_metric(self):
        """
        Evaluation function
        :return: the overall averaged value of Precision
        """
        return {u: MRR.__user_mrr(u_r, self._cutoff, self._relevant_items[u])
             for u, u_r in self._recommendations.items()}
