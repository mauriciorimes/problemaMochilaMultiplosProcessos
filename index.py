#!pip install mpi4py

import time as t
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

#%%writefile mochila_serial.py
# Importando as bibliotecas
import time as t
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
# Importando as bibliotecas
import random
import sys
from mpi4py import MPI

random.seed(1)

start_time = t.time()
comm = MPI.COMM_WORLD
pid      = comm.Get_rank()          #PID do Processos atual
numProcs = comm.Get_size()          #total de processos iniciados
MaqNome  = MPI.Get_processor_name() #Nome da máquina

# Definições
CAP_MOC = int(sys.argv[1])   # 30
TAM_LOJA = int(sys.argv[2])  # 5
QTD_PROD = int(sys.argv[3])  # 3
MAX_PRECO = int(sys.argv[4]) #20
MAX_VOL = int(sys.argv[5])   #10

# Gerador de combinações
def conv_base(num, base, exp):
    valor = num
    saida=[]
    while valor > 0:
        saida.append(valor % base)
        valor = valor // base
    while len(saida) < exp:
        saida.append(0)
    saida = [saida[len(saida)-i-1] for i in range(len(saida))] 
    return saida

#Gerando o intervalo das combinações
def gera_inter(base, exp, inicio, fim):
    saida=[]
    for i in range(inicio, fim):
        saida.append(conv_base(i, base, exp))
    return(saida)

#Gerando a loja
def gera_loja(tam, max_preco, max_vol):
    loja=[]
    for i in range(tam):
        loja.append((random.randint(1, max_preco), random.randint(1, max_vol)))
    return loja

# Cálculo do custo e volume da combinação
def custo_vol(loja, comb):
    custo = 0
    vol = 0
    for i in range(len(loja)):
        custo += loja[i][0] * comb[i]
        vol += loja[i][1] * comb[i]
    return (custo, vol)

#gerando a loja
loja = gera_loja(TAM_LOJA, MAX_PRECO, MAX_VOL)
#print(loja) #debug

comb = gera_inter(QTD_PROD, TAM_LOJA, 0, QTD_PROD**TAM_LOJA)
#print(comb) #comeca aqui

if pid == 0:
    print("PROCESSO: ", comm.Get_rank())
    maxOfRangeCombs = int((len(comb))/(numProcs - 1))
    inicio = 0
    ultimo = (len(comb))%(numProcs - 1)
    for i in range(1, numProcs):
        if (i == (numProcs - 1)):
            rangeOfComb = [inicio, (((maxOfRangeCombs * i)) + ultimo)]
        else:
            rangeOfComb = [inicio, ((maxOfRangeCombs * i) - 1)]
        comm.send(rangeOfComb, dest=i)
        inicio = (maxOfRangeCombs * i) - 1
    print(loja)
else:
    posicaoMax = 0
    max = (0, 0)
    max_comb = []
    rangeOfTeste = comm.recv(source=0)
    print("PROCESSO: ",comm.Get_rank())
    print(rangeOfTeste)
    rangeOfTeste = range(rangeOfTeste[0],rangeOfTeste[1])
    for teste in rangeOfTeste:
        resp = custo_vol(loja, comb[teste])
        if resp[0] >= max[0] and resp[1] <= CAP_MOC:
            max = resp
            max_comb = comb[teste]
            posicaoMax = teste
    print("max_comb = ",max_comb)
    print("max = ",max)
    print("")
    comm.send(posicaoMax, dest=0)
if pid == 0:
    vetorPosicaoMax = []
    posicaoMax = 0
    valorMax = 0
    for i in range(1, numProcs):
        vetorPosicaoMax.append(comm.recv(source=i))
    for j in vetorPosicaoMax:
        if (custo_vol(loja, comb[j])[0] >= valorMax):
            posicaoMax = j
            valorMax = custo_vol(loja, comb[j])[0]
    print("Valor máximo final = ",valorMax)
    print("Melhor combinação final = ",comb[posicaoMax])
        
#print(f'---Tempo de execução do processo {pid}: {(t.time() - start_time)} seconds ---')
#print('-------------------------------------------------------------------')
#print('')

#!mpiexec --oversubscribe --allow-run-as-root -np 4 python mochila_serial.py 30 5 11 20 10
