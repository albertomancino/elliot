"""
This is the implementation of the Precision metric.
It proceeds from a user-wise computation, and average the values over the users.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import numpy as np
from ..base_metric import BaseMetric


class DSC(BaseMetric):
    """
    This class represents the implementation of the F-score recommendation metric.
    Passing 'F1' to the metrics list will enable the computation of the metric.
    """

    def __init__(self, recommendations, config, params, eval_objects, additional_data):
        """
        Constructor
        :param recommendations: list of recommendations in the form {user: [(item1,value1),...]}
        :param cutoff: numerical threshold to limit the recommendation list
        :param relevant_items: list of relevant items (binary) per user in the form {user: [item1,...]}
        """
        super().__init__(recommendations, config, params, eval_objects, additional_data)
        self._cutoff = self._evaluation_objects.cutoff
        self._relevant_items = self._evaluation_objects.relevance.get_binary_relevance()
        self._beta = self._additional_data['beta']
        self._squared_beta = self._beta**2

    @staticmethod
    def name():
        """
        Metric Name Getter
        :return: returns the public name of the metric
        """
        return "DSC"

    @staticmethod
    def __user_dsc(user_recommendations, cutoff, user_relevant_items, squared_beta):
        """
        Per User F-score
        :param user_recommendations: list of user recommendation in the form [(item1,value1),...]
        :param cutoff: numerical threshold to limit the recommendation list
        :param user_relevant_items: list of user relevant items in the form [item1,...]
        :return: the value of the Precision metric for the specific user
        """
        p = sum([1 for i in user_recommendations[:cutoff] if i[0] in user_relevant_items]) / cutoff
        r = sum([1 for i in user_recommendations[:cutoff] if i[0] in user_relevant_items]) / min(len(user_relevant_items), cutoff)
        num = (1 + squared_beta) * p * r
        den = (squared_beta * p) + r
        return num/den if den != 0 else 0

    def eval(self):
        """
        Evaluation function
        :return: the overall averaged value of F-score
        """
        return np.average(
            [DSC.__user_dsc(u_r, self._cutoff, self._relevant_items[u], self._squared_beta)
             for u, u_r in self._recommendations.items()]
        )

    def eval_user_metric(self):
        """
        Evaluation function
        :return: the overall averaged value of F-score
        """
        return {u: DSC.__user_dsc(u_r, self._cutoff, self._relevant_items[u], self._squared_beta)
             for u, u_r in self._recommendations.items()}
