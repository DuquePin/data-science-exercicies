import streamlit as st
import re
import pickle
import io
import joblib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, roc_curve, confusion_matrix)


# Cache for loading data
@st.cache_data
def load_data(file_path, file_type):
    try:
        if file_type == 'ftr':
            return pd.read_feather(file_path)
        elif file_type == 'csv':
            return pd.read_csv(file_path)
        elif file_type == 'xlsx':
            return pd.read_excel(file_path)
        else:
            raise ValueError('Unsupported file type.')
    except Exception as exc:
        st.error(f'Error loading data: {exc}')
        return None


# Cache for sampling data
@st.cache_data
def sample_data(df, sample_size):
    try:
        return df.sample(n=sample_size, random_state=412)
    except Exception as exc:
        st.error(f'Error sampling data: {exc}')
        return None


# Cache for loading model
@st.cache_resource
def load_model(uploaded_file):
    try:
        if uploaded_file is None:
            st.error('No file uploaded.')
            return None

        bytes_data = uploaded_file.getvalue()
        model = joblib.load(io.BytesIO(bytes_data))

        if model is None:
            raise ValueError('Loaded model is None. Check the file integrity.')

        return model
    except pickle.UnpicklingError:
        st.error('Error: The file is not a valid pickle file or is corrupted.')
        return None
    except Exception as exc:
        st.error(f'An unexpected error occurred: {exc}')
        return None


# Function to score the model
def score_model(model, df, feature_selection, target_column):
    try:
        if model is None or df is None:
            st.error('Model or dataset not available for scoring.')
            return None, None

        # Separate the data into features (X) and target (y)
        X = df[feature_selection]
        y = df[target_column]

        # Create predictions and probability predictions
        y_predict = model.predict(X)
        y_proba = model.predict_proba(X)

        fpr, tpr, _ = roc_curve(y, y_proba[:, 1])

        # Compute metrics
        metrics = {
            'Accuracy': accuracy_score(y, y_predict),
            'Precision': precision_score(y, y_predict, average='weighted', zero_division=0),
            'Recall': recall_score(y, y_predict, average='weighted', zero_division=0),
            'F1 Score': f1_score(y, y_predict, average='weighted', zero_division=0),
            'AUC Score': roc_auc_score(y, y_predict, average='weighted'),
            'Gini Coefficient': 2 * roc_auc_score(y, y_predict, average='weighted') - 1,
            'KS Statistic': max(tpr - fpr)
        }

        # Compute confusion matrix
        cm = confusion_matrix(y, y_predict)
        return metrics, cm
    except Exception as exc:
        st.error(f'An unexpected error occurred while scoring the model: {exc}')
        return None, None


# Function to plot confusion matrix
def plot_confusion_matrix(cm, class_labels):
    fig, ax = plt.subplots(figsize=(8, 6))  # Adjusted figure size
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_labels, yticklabels=class_labels)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    st.pyplot(fig)


# Main application function
def main():
    st.set_page_config(page_title='Credit Scoring', layout='wide')
    st.title('Credit Scoring Application')

    # Upload database
    st.write('---')
    st.subheader('Upload Credit Scoring Database')

    fp = st.file_uploader('Upload a dataset:', type=['ftr', 'csv', 'xlsx'])
    database_df = None

    if fp is not None:
        match = re.search(r'\.([a-zA-Z0-9.]+)$', fp.name)
        if match:
            file_ext = match.group(1)
            database_df = load_data(fp, file_ext)

            if database_df is not None:
                st.success('Data loaded successfully!')
                st.subheader('Preview of Data')
                st.write(database_df.head())
            else:
                st.error('Failed to load the dataset.')
        else:
            st.error('Invalid file extension. Please upload a valid file.')

    # Sampling section
    st.write('---')
    st.subheader('Sample Database')
    sample_fraction = st.slider(label='Select Sample Fraction:', min_value=0.1, max_value=1.0, step=0.1)

    sample_database_df = None
    if database_df is not None:
        sample_size = round(database_df.shape[0] * sample_fraction)
        sample_database_df = sample_data(database_df, sample_size)

        st.write(f'Sample size: **{sample_size}** rows ({sample_fraction:.2%} of the dataset).')
        st.write(sample_database_df.head())

    # Selecting features section
    st.write('---')
    st.subheader('Select Target and Feature Variables')

    if sample_database_df is not None:
        target_column = st.selectbox('Select Target', options=sample_database_df.columns,
                                     index=len(sample_database_df.columns) - 1)
        feature_selection = st.multiselect('Select Features:',
                                           options=sample_database_df.drop(columns=[target_column]).columns,
                                           default=sample_database_df.drop(columns=[target_column]).columns)

        if len(feature_selection) == 0:
            st.warning('Please select at least one feature.')

        st.write(f'Target variable: **{target_column}**')
        st.write(f'Selected features: **{", ".join(feature_selection)}**')

    # Upload model
    st.write('---')
    st.subheader('Upload Credit Scoring Model')
    uploaded_model_file = st.file_uploader('Upload a model (.pkl):', type=['pkl'])

    model = None
    if uploaded_model_file is not None:
        model = load_model(uploaded_model_file)
        if model is not None:
            st.success('Model loaded successfully!')

    # Scoring button
    st.write('---')
    if model is not None and sample_database_df is not None:
        if st.button('Score Model'):
            st.subheader('Model Performance Metrics')
            metrics, cm = score_model(model, sample_database_df, feature_selection, target_column)

            if metrics:
                for metric, value in metrics.items():
                    if metric in ['Gini Coefficient', 'KS Statistic']:
                        st.write(f'**{metric}:** {value:.4f}')
                        continue
                    st.write(f'**{metric}:** {value:.4%}')

                # Confusion matrix visualization
                class_labels = sorted(sample_database_df[target_column].unique())
                st.subheader('Confusion Matrix')
                plot_confusion_matrix(cm, class_labels)


if __name__ == '__main__':
    main()
