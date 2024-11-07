import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO


# noinspection PyBroadException
@st.cache_data
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)


@st.cache_data
def multiselect_filter(data, col, selected_cols):
    if 'all' in selected_cols:
        return data
    else:
        return data[data[col].isin(selected_cols)].reset_index(drop=True)


# noinspection PyTypeChecker
@st.cache_data
def convert_to_excel(dataframe):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


# noinspection PyBroadException
def main():
    global databank_target_perc

    st.set_page_config(page_title='Telemarketing analysis',
                       page_icon='telemarketing_icon.png',
                       layout='wide',
                       initial_sidebar_state='expanded'
                       )

    st.write('# Telemarketing analysis')
    st.markdown('---')

    st.write('## Purpose')
    st.write('This is an application to manipulate data from')

    st.sidebar.image(Image.open('Bank-Branding.jpg'))
    st.sidebar.write('## Upload file')
    fp = st.sidebar.file_uploader('Bank marketing data', type=['csv', 'xlsx'])

    if fp is not None:
        databank_raw = load_data(fp)
        databank = databank_raw.copy()

        st.write('## Raw Data')
        st.write(databank_raw.head())

        with st.sidebar.form(key='filter_form'):
            graph_type = st.radio('Graph Type:', ('Bar', 'Pie'))
            ages_slider = st.slider(label='Age Filter',
                                    min_value=int(databank.age.min()),
                                    max_value=int(databank.age.max()),
                                    value=(int(databank.age.min()), int(databank.age.max())),
                                    step=1)

            mapping = dict()

            obj_columns = [col for col in databank if databank[col].dtype == 'O']
            st.write(obj_columns)

            for col in obj_columns:
                mapping[f'{col}_list'] = databank[col].unique().tolist()
                mapping[f'{col}_list'].append('all')
                mapping[f'{col}_selected'] = st.multiselect(col.capitalize(), mapping[f'{col}_list'], ['all'])

            st.write(mapping)

            databank = databank.query('age >= @ages_slider[0] and age <= @ages_slider[1]')

            for column in obj_columns:
                selected_value = mapping[f'{column}_selected']
                databank = databank.pipe(multiselect_filter, column, selected_value)

            submit_button = st.form_submit_button(label='Apply')

        st.write('## Processed Data')
        st.write(databank.head())

        st.download_button(label='📥 Download processed data as EXCEL file',
                           data=convert_to_excel(databank),
                           file_name='bank_processed.xlsx')

        st.markdown('---')
        databank_raw_target_perc = (databank_raw.y.value_counts(normalize=True).to_frame() * 100).sort_index()

        try:
            databank_target_perc = (databank.y.value_counts(normalize=True).to_frame() * 100).sort_index()
        except:
            st.error('Filter error')

        col1, col2 = st.columns(2)

        col1.write('### Original Data Proportion')
        col1.write(databank_raw_target_perc)

        col1.download_button(label='📥 Download as EXCEL file',
                             data=convert_to_excel(databank_raw_target_perc),
                             file_name='bank_raw_y.xlsx')

        col2.write('### New Data Proportion')
        col2.write(databank_target_perc)

        col2.download_button(label='📥 Download as EXCEL file',
                             data=convert_to_excel(databank_target_perc),
                             file_name='bank_y.xlsx')
        st.markdown('---')
        st.write('## Acceptance ratio')

        if graph_type == 'Bar':
            fig, ax = plt.subplots(1, 2, figsize=(5, 3), sharey=True)

            sns.barplot(data=databank_raw_target_perc,
                        x='y',
                        y='proportion',
                        palette=['#1E90FF', '#FFA500'],
                        ax=ax[0])

            ax[0].set_title('Raw data',
                            fontweight='bold')

            ax[0].set_xlabel('Acceptance')
            ax[0].set_ylabel('Proportion %')

            sns.barplot(data=databank_target_perc,
                        x='y',
                        y='proportion',
                        palette=['#1E90FF', '#FFA500'],
                        ax=ax[1])

            ax[1].set_title('Processed data',
                            fontweight='bold')

            ax[1].set_xlabel('Acceptance')
            ax[1].set_ylabel('Proportion %')

            plt.tight_layout()
        else:
            df = pd.concat([databank_raw_target_perc, databank_target_perc], axis=1)

            axes = df.plot.pie(
                subplots=True,
                figsize=(8, 4),
                autopct='%1.1f%%',
                startangle=90,
                colors=['#1E90FF', '#FFA500']
            )

            axes[0].set_title('Raw Data',
                              fontweight='bold')

            axes[1].set_title('Processed Data',
                              fontweight='bold')

            for ax in axes:
                ax.set_ylabel('')

            plt.tight_layout()

        st.pyplot(plt)


if __name__ == '__main__':
    main()
