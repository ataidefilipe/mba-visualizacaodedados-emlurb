from tratamento import tratamento_dados

df = tratamento_dados()

#TOTALIZADOR POR SITUACAO
total_situacao = df['SITUACAO'].value_counts()
print("Total por Situação:")
print(total_situacao)

print("ordem sit: ",df['ORDEM_SITUACAO'].unique())