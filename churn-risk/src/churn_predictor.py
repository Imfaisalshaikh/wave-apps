import h2o
from h2o.estimators.gbm import H2OGradientBoostingEstimator


class ChurnPredictor:
    """
    Wrapper for H2O-3

    ChurnPredictor builds an abstraction between H2O-3 machine learning library and the Churn Risk app
    giving the developer freedom to integrate any 3rd party machine library with a minimal change to the app code.
    """

    def __init__(self):
        self.model = None
        self.train_df = None
        self.test_df = None
        self.predicted_df = None
        self.contributions_df = None

        h2o.init()

    def build_model(self, training_data_path, model_id):
        train_df = h2o.import_file(
            path=training_data_path, destination_frame="telco_churn_train.csv"
        )

        predictors = train_df.columns
        response = "Churn?"
        train, valid = train_df.split_frame([0.8])

        self.model = H2OGradientBoostingEstimator(model_id=model_id, seed=1234)
        self.model.train(
            x=predictors, y=response, training_frame=train, validation_frame=valid
        )

    def set_testing_data_frame(self, testing_data_path):
        self.test_df = h2o.import_file(
            path=testing_data_path, destination_frame="telco_churn_test.csv"
        )

    def predict(self):
        self.predicted_df = self.model.predict(self.test_df)
        self.contributions_df = self.model.predict_contributions(self.test_df)

    def get_churn_rate_of_customer(self, row_index):
        """
        Return the churn rate of given customer as a percentage.

        :param row_index: row index of the customer in dataframe
        :return: percentage as a float
        """
        return round(
            float(self.predicted_df.as_data_frame()["TRUE"][row_index]) * 100, 2
        )

    def get_shap_explanation(self, row_index):
        return self.model.shap_explain_row_plot(frame=self.test_df, row_index=row_index)

    def get_top_negative_pd_explanation(self, row_index):
        """
        Return the partial dependence explanation of the top negatively contributing feature.

        :param row_index: row index to select from H2OFrame for the explanation
        :return: matplotlib figure object
        """
        # column_index = self.contributions_df.idxmin(axis=1).as_data_frame()[
        #     "which.min"
        # ][row_index]

        # Using Pandas DataFrame.idxmin() until https://h2oai.atlassian.net/browse/PUBDEV-7906 is fixed
        pdf = self.contributions_df.as_data_frame()
        del pdf["BiasTerm"]  # Delete bias column added by predict_contributions()
        min_column_name = pdf.idxmin(axis=1)[row_index]

        return self.model.pd_plot(
            frame=self.test_df,
            row_index=row_index,
            column=min_column_name,
        )

    def get_top_positive_pd_explanation(self, row_index):
        """
        Return the partial dependence explanation of the top positively contributing feature.

        :param row_index: row index to select from H2OFrame for the explanation
        :return: matplotlib figure object
        """
        column_index = self.contributions_df.idxmax(axis=1).as_data_frame()[
            "which.max"
        ][row_index]
        return self.model.pd_plot(
            frame=self.test_df,
            row_index=row_index,
            column=self.test_df.col_names[column_index],
        )
