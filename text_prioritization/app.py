from warnings import filterwarnings

filterwarnings("ignore")

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from io import BytesIO

from ticket_prioritization.pipeline import preprocess_pipeline
from ticket_prioritization.processors import display_metrics
from imblearn.pipeline import Pipeline as Imblearn_pipeline

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from imblearn.over_sampling import SMOTE
from sklearn.feature_extraction.text import HashingVectorizer
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.feature_extraction.text import TfidfVectorizer

import time
import uvicorn
import joblib
import pandas as pd

app = FastAPI()


class ShortDescription(BaseModel):
    description: str


try:
    model = joblib.load("models/model_pipeline.joblib")
except FileNotFoundError:
    print("Model not trained yet")


@app.post("/preprocess/")
def preprocess_data(file: UploadFile = File(...)):
    if file.filename.endswith((".csv", ".CSV")):
        csv_file = file.file.read()
        df = pd.read_csv(BytesIO(csv_file))
        output = preprocess_pipeline.transform(X=df)

        output.to_csv("data/preprocessed_data.csv", index=False)
        return {
            "Message": "Preprocessed data saved to data/preprocessed_data.csv"
        }
    else:
        return {
            "Message": "Please upload a csv file"
        }


@app.post("/train/")
def train_model(file: UploadFile = File(...)):
    if file.filename.endswith((".csv", ".CSV")):
        csv_file = file.file.read()
        df = pd.read_csv(BytesIO(csv_file))

        X = df["short_descriptions"].values.astype("U")
        y = df["priority"]

        enc = LabelEncoder()
        y_enc = enc.fit_transform(y)
        # joblib.dump(value=enc, filename="models/encoder.joblib")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=0
        )

        X_test, X_val, y_test, y_val = train_test_split(
            X_test, y_test, test_size=0.5, random_state=0
        )

        print(
            X_train.shape,
            y_train.shape,
            X_test.shape,
            y_test.shape,
            X_val.shape,
            y_val.shape,
        )

        val_df = pd.DataFrame(
            {
                "short_descriptions": X_val,
                "priority": y_val
            }
        ).to_csv(
            "data/validation_set.csv",
            index=False
        )

        models = [
            MultinomialNB(), 
            LogisticRegression(n_jobs=-1, random_state=0),
            RandomForestClassifier(n_jobs=-1),    
            LinearSVC(random_state=0),
            DecisionTreeClassifier(),
        ]

        trained_models = dict()
        print("-" * 50)
        for m in models:
            model_name = m.__class__.__name__
            print(f"Training -> {model_name}")

            train_pipeline = Imblearn_pipeline(
                [
                    (
                        "hash_vectorizing", HashingVectorizer(n_features=30000, 
                            alternate_sign=False)   #alternate_sign is set to False for Naive Bayes classifier
                    ),
                    (
                        "smote_over_sampling", SMOTE(random_state=0,
                            n_jobs=-1)
                    ),
                    (
                        "classification_model_fit", m
                    ),
                ]
            )

            s = time.time()

            predictor = train_pipeline
            predictor.fit(X_train, y_train)

            e = time.time()
            print(f"Training time: {round(e - s)} seconds")

            preds = predictor.predict(X_test)
            acc, f1, precision, recall = display_metrics(true=y_test,
                                                         pred=preds)

            trained_models[f1] = predictor

            print("-" * 50)

        final_model = max(sorted(trained_models.items(), reverse=True))[1]
        print("Best model: ", final_model)

        y_hat = final_model.predict(X_test)

        acc, f1, precision, recall = display_metrics(true=y_test, pred=y_hat)

        joblib.dump(
            value=final_model, filename="models/train_pipeline.joblib",
            compress=3
        )

        try:
            model = joblib.load("models/train_pipeline.joblib")
        except FileNotFoundError:
            print("Model not trained yet")

        report = classification_report(
            y_true=y_test, y_pred=final_model.predict(X_test), output_dict=True
        )
        report_df = pd.DataFrame(report)

        report_df.T.to_csv("data/classification_report.csv")
        name_of_model = final_model.get_params()[
            "classification_model_fit"].__class__.__name__
        print(f"Pipeline params: {name_of_model}")

        return {
            "Model_name": name_of_model,
            "Accuracy": acc,
            "F1": f1,
            "Precision": precision,
            "Recall": recall,
        }

    else:
        return {"Message": "Please upload a csv file"}


@app.post("/predict_single/")
async def predict_asgn_group(short_desc: ShortDescription):
    short_desc_dict = short_desc.dict()

    if short_desc.description:
        prediction = model.predict([short_desc.description])
        print(prediction)

        prediction_enc = prediction[0]
        short_desc_dict.update(
            {"Predicted assignment group": str(prediction_enc)})

    return short_desc_dict


@app.post("/predict_batch/")
async def batch_predictions(file: UploadFile = File(...)):
    try:
        if file.filename.endswith((".csv", ".CSV")):
            csv_file = await file.read()
            df = pd.read_csv(BytesIO(csv_file))
            df.dropna(inplace=True)

            X = df["short_descriptions"].values
            y = df["priority"].values

            pred_asgn_grps = model.predict(X)
            pred_asgn_grps_enc = pred_asgn_grps

            output = list()
            for short_desc, true_grp, pred_grp in zip(
                    X[:50], y[:50], pred_asgn_grps_enc[:50]
            ):
                result = dict()
                result["short_descriptions"] = short_desc
                result["true_priority"] = true_grp
                result["pred_priority"] = pred_grp
                output.append(result)

            return output

        else:
            return {"Error": "Please upload a csv file"}

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0',port=5000)
