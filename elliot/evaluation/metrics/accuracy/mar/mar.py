"""
This is the implementation of the Mean Average Recall metric.
It proceeds from a user-wise computation, and average the values over the users.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import numpy as np
from evaluation.metrics.base_metric import BaseMetric


class MAR(BaseMetric):
    """
    This class represents the implementation of the Mean Average Recall recommendation metric.
    Passing 'MAR' to the metrics list will enable the computation of the metric.
    """

    def __init__(self, recommendations, config, params, eval_objects):
        """
        Constructor
        :param recommendations: list of recommendations in the form {user: [(item1,value1),...]}
        :param config: SimpleNameSpace that represents the configuration of the experiment
        :param params: Parameters of the model
        :param eval_objects: list of objects that may be useful for the computation of the different metrics
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
        return "MAR"

    @staticmethod
    def __user_ar(user_recommendations, cutoff, user_relevant_items):
        """
        Per User Average Recall
        :param user_recommendations: list of user recommendation in the form [(item1,value1),...]
        :param cutoff: numerical threshold to limit the recommendation list
        :param user_relevant_items: list of user relevant items in the form [item1,...]
        :return: the value of the Recall metric for the specific user
        """
        return np.average([MAR.__user_recall(user_recommendations[:cutoff], (n+1), user_relevant_items) for n in range(cutoff)])

    @staticmethod
    def __user_recall(user_recommendations, cutoff, user_relevant_items):
        """
        Per User Recall
        :param user_recommendations: list of user recommendation in the form [(item1,value1),...]
        :param cutoff: numerical threshold to limit the recommendation list
        :param user_relevant_items: list of user relevant items in the form [item1,...]
        :return: the value of the Recall metric for the specific user
        """
        return sum([1 for i in user_recommendations if i[0] in user_relevant_items]) / min(len(user_relevant_items), cutoff)

    def eval(self):
        """
        Evaluation function
        :return: the overall averaged value of Mean Average Recall
        """
        return np.average(
            [MAR.__user_ar(u_r, self._cutoff, self._relevant_items[u])
             for u, u_r in self._recommendations.items() if len(self._relevant_items[u])]
        )

    def eval_user_metric(self):
        """
        Evaluation function
        :return: the overall averaged value of Mean Average Recall per user
        """
        return {u: MAR.__user_ar(u_r, self._cutoff, self._relevant_items[u])
             for u, u_r in self._recommendations.items() if len(self._relevant_items[u])}
