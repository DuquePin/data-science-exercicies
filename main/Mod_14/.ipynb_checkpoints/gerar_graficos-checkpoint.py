import sys

def main():
    if len(sys.argv) > 3:
        months = sys.argv[3:]
        if validate_long_entry(months):
            if confirm_months(months):
                gen_plots(months)
            else:
                return None
        else:
            return None
    else:
        months = get_months()
        if confirm_months(months):
            gen_plots(months)
        else:
            return None     

def get_months():
    print("Digite meses separados por vírgula (ABR, MAR, JUN, etc):")
    while True:
        entry = input("> ").strip()
        if validate_long_entry(entry.split(",")):
            entry = entry.split(",")
            entry = [item.strip().upper() for item in entry]
            return entry
        else:
            print("Entrada invalida. Tente novamente.")

def validate_long_entry(entry):
    for item in entry:
        if item.strip().upper() not in ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]:
            return False
    return True

def confirm_months(months):
    print("Você digitou: ", months)
    print("Confirma? [s/n]")
    print("(Caso não seja a lista correta, o script vai fechar automaticamente)")
    while True:
        confirm = input("> ").strip().lower()
        if confirm == "s":
            return True
        elif confirm == "n":
            return False
        else:
            print("Inválido. Tente novamente.")
    

def gen_plots(selected_months):
    import os
    import pandas as pd 
    import seaborn as sns
    import matplotlib.pyplot as plt
    
    dataset = pd.read_csv('./input/SINASC_RO_2019.csv')
    dataset = dataset[['IDADEMAE', 'SEXO', 'APGAR1', 
                       'APGAR5', 'PESO', 'CONSULTAS', 
                       'DTNASC', 'GESTACAO', 'GRAVIDEZ', 
                       'ESCMAE', 'IDADEPAI']]
    dataset = split_months(dataset, selected_months)

    if not os.path.exists("./output"):
        os.makedirs("./output")

    for month in selected_months:
        dataset[month]['DTNASC'] = pd.to_datetime(dataset[month]['DTNASC'])
        dataset[month]['DIA_SEMANA'] = dataset[month]['DTNASC'].dt.dayofweek
        dataset[month]['DIA_SEMANA'] = dataset[month]['DIA_SEMANA'].map({0: 'SEG', 1: 'TER', 2: 'QUA', 3: 
                                                                   'QUI', 4: 'SEX', 5: 'SAB', 6: 'DOM'})
    
        fig, ax = plt.subplots(figsize=(15, 5))
        agg_data = pd.pivot_table(dataset[month], 
                                  values='IDADEMAE', 
                                  index='DIA_SEMANA', 
                                  columns='SEXO', 
                                  aggfunc='count')
        sns.lineplot(agg_data, ax=ax)
        ax.set_xlabel('Dias da Semana')
        ax.set_ylabel('Quantidade de Nascimentos')
        ax.set_title('Quantidade de Nascimento por Dia da Semana Dividido por Sexo\n({})'.format(month))
        plt.savefig('./output/plot_{}.png'.format(month))

def split_months(dataset, selected_months):
    from pandas import to_datetime
    dataset['DTNASC'] = to_datetime(dataset['DTNASC'])
    dataset['MES'] = dataset['DTNASC'].dt.month
    dataset['MES'] = dataset['MES'].map({1: 'JAN', 2: 'FEV', 3: 'MAR', 4:'ABR', 5: 'MAI', 6: 'JUN', 
                                         7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'})
    dfs_per_month = {month: df_month for month, df_month in dataset.groupby('MES')}
    
    only_selected_months = {month: dfs_per_month[month] for month in selected_months if month in dfs_per_month}

    return only_selected_months
            
    
if __name__ == "__main__":
    main()
