### Ticket Prioritization

Dataset

For this feature, we have used the short descriptions and priority columns available in the given ticket dumps.
There are 7 ticket dumps in the form of excel files, out of which 3 files contains the information about the short descriptions and priority required to build the priority classification model.
After combining these 3 files, we have around 164,000 datapoints. Which contains following 17 categories,
'1 - Critical', '1 - Urgent', '2 - High',

'2 - Normal', '3 - Moderate', '4 - Low',

'5 - Minor', 'CRITICAL', 'HIGH',

'LOW', 'MEDIUM', 'PROJECT',

'Priority 1', 'Priority 2', 'Priority 3',

'Priority 4', 'Service Request'

We re-arranged these categories into 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW' as follows,
'4 - Low', '5 - Minor' --> 'LOW'
'3 - Moderate', '2 - Normal', 'Priority 4' --> 'MEDIUM'
'Priority 2', 'Priority 3', '2 - High' --> 'HIGH'
'Priority 1',  '1 - Critical', '1 - Urgent' --> 'CRITICAL'
and dropped 'PROJECT' and 'Service Request' as they are not required for our model.

To balance this dataset, we used an over sampling technique called SMOTE (Synthetic Minority Oversampling), which is based upon KNN algorithm.
 

Preprocessing pipeline

The preprocessing pipeline is built using sklearn pipelines module.
In order to build the model, we have to clean and vectorize the short descriptions as we are using it as the feature. The steps for preprocessing are,
Lowercasing the text
Removing punctuations and words containing numbers
Removing error characters from the text
Removing multiple space from the text
Removing short descriptions with less than 2 words
 

Training pipeline

The training pipeline is built using imbalanced-learn pipelines module.
Due to the limitations of partial fit method available in only a few algorithms, we have to train the models from scratch every time we'll want to update the model.
In order to vectorize the short descriptions text, due to the size of sparse matrices generated from Count vectorizers and TfIdf vectorizers, we've used Hashing vectorizer in order to save the memory in production environment.
We have divided our dataset into 80% training, 10% testing and 10% validation sets.
This pipeline fits multiple classification algorithms and gives us the best one based on F1 score of the fitted model. Due to this our approach is dependent on the nature of data and not a specific classification algorithm.
Based on the currently available data, the best model we have is Random_forest with default hyperparameters which is giving us around 78% accuracy score and 79% F1 score.
The overall time taken to fit Logistic Regression, Random_forest, LinearSVM, and DecisionTree classifiers was about 1 hour on a 4th Gen i5 8GB system, with the overall peak memory footprint of about 1250MB.
 

And following are the API endpoint details,

 

There are 4 endpoints,

 

Preprocess

Endpoint: “/preprocess/”

HTTP request: POST

Input: Form data, {‘file’: csv file}

Output: JSON,

{

    "Message": "Preprocessed data saved to data/preprocessed_data.csv"

}

Description: This endpoint takes a csv file containing short descriptions and ticket priority labels, performs above mentioned preprocessing steps and saves the preprocessed csv file in the “data” folder.

 

Train

            Endpoint: “/train/”

            HTTP request: POST

Input: Form data, {‘file’: preprocessed csv file}

Output: JSON,

{

    "Model_name": "RandomForestClassifier",

    "Accuracy": 78.21,

    "F1": 79.675,

    "Precision": 81.12,

    "Recall": 78.23

}

Description: This endpoint takes the preprocessed csv file and creates 80-10-10 train-test-val splits. Stores the validation split in a csv file. Fits various classifiers and chooses the best on the basis of F1 score, returns information about best model as a JSON response and saves this pipeline in a joblib file.

 

Predict Single

            Endpoint: “/predict_single/”

            HTTP request: POST

            Input: JSON,

{

    "description": "coin capex online integrated management"

}

            Output: JSON,

{

    "description": "coin capex online integrated management",

    "Predicted assignment group": "MEDIUM"

}

 

Predict Batch

                Endpoint: “/predict_batch/”

                HTTP request: POST

                Input: Form data, {‘file’: validation csv file}

                Output: JSON,

[

    {

        "short_descriptions": "can no longer login to jira",

        "true_priority": "LOW",

        "pred_priority": "LOW"

    },

    {

        "short_descriptions": "cproject resources tab staffing” and “mrs is missing",

        "true_priority": "LOW",

        "pred_priority": "LOW"

    },

    {

        "short_descriptions": "need new laptop asap see ",

        "true_priority": "MEDIUM",

        "pred_priority": "MEDIUM"

    },

        ………….

]
