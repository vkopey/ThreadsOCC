# -*- coding: utf-8 -*-
"""Читає дані з файлу результатів CalculiX .frd
!Увага! Читає тільки 1 інкремент з напруженнями,
тому застосовуйте *TIME POINTS
"""
file=r'model.frd'

def parseLines(startLine):
    "Читає дані з блоку що починається з startLine"
    res={} # напруження для кожного вузла
    inside=False #чи всередині блоку
    with open(file,'r') as f:
        for ln in f: #для економії памяті
            if ln.startswith(startLine): #початок блоку
                inside=True
            if inside: # всередині блоку  
                r=parseLine(ln)
                if r!=None: res[r[0]]=r[1]
            if inside and ln==' -3\n': break #кінець блоку
    return res
            
def parseLine(ln): # парсить рядок з напруженнями вузла
    if not ln.startswith(" -1"): return
    nodeRes=[]
    s=ln.strip()
    for i in range(7): # розбити рядок на 7 частин по 12 символів
        nodeRes.append(s[12*i:12*i+12])
    node=int(nodeRes[0][2:]) # вузол
    r=[float(i) for i in nodeRes[1:]] # значення
    return node,r 

def stressMises(Sx,Sy,Sz,Txy,Tyz,Txz):
    "Екв. напруження за критерієм Мізеса"
    #(1/2**0.5)*((Sx-Sy)**2+(Sy-Sz)**2+(Sz-Sx)**2+6*Txy**2+6*Tyz**2+6*Txz**2)**0.5
    return (Sx*Sx + Sy*Sy + Sz*Sz - Sx*Sy - Sx*Sz - Sy*Sz + 3*Txy*Txy + 3*Txz*Txz + 3*Tyz*Tyz)**0.5

def principalStress(Sx,Sy,Sz,Sxy,Syz,Szx):
    a=((Sx-Sy)**2/4+Sxy**2)**0.5
    S=[(Sx+Sy)/2+a, Sz, (Sx+Sy)/2-a]
    S.sort(reverse=True)
    return S 

def principalStress_(Sx,Sy,Sz,Sxy,Syz,Szx):# for test only
    def fn(S,Sx,Sy,Sz,Sxy,Syz,Szx):
        Syz=0.0;Szx=0.0
        #S**3-(Sx+Sy+Sz)*S**2+(Sx*Sy+Sy*Sz+Sz*Sx-Sxy**2-Syz**2-Szx**2)*S-(Sx*Sy*Sz+2*Sxy*Syz*Szx-Sx*Syz**2-Sy*Szx**2-Sz*Sxy**2)
        return S**3-(Sx+Sy+Sz)*S**2+(Sx*Sy+Sy*Sz+Sz*Sx-Sxy**2)*S-(Sx*Sy*Sz-Sz*Sxy**2)
    
    from scipy import arange
    from scipy.optimize import fsolve
    S=fsolve(fn, arange(-1000., 1000., 200.), args=(Sx,Sy,Sz,Sxy,Syz,Szx))
    S=list(set([round(i,2) for i in S]))
    S.sort(reverse=True)
    return S

def FOS(S1_2, S1_1, S2_2, S2_1, S3_2, S3_1):
    """Розраховує коефіцієнт запасу втомної міцності за критерієм Сайнса
S1_2 - головне напруження 1 крок 2 (максимальне навантаження), МПа
S1_1 - головне напруження 1 крок 1 (мінімальне навантаження)
"""
    sn = 207.0 #границя витривалості
    m = 1.0 #коефіцієнт
    
    Sm3 = (S3_2 + S3_1) / 2.
    Sa3 = (S3_2 - S3_1) / 2.
    
    Sm2 = (S2_2 + S2_1) / 2.
    Sa2 = (S2_2 - S2_1) / 2.
    
    Sm1 = (S1_2 + S1_1) / 2.
    Sa1 = (S1_2 - S1_1) / 2.
    
    FOS = (sn - m * (Sm1 + Sm2 + Sm3) / 3.) / (((Sa1 - Sa2) ** 2 + (Sa2 - Sa3) ** 2 + (Sa3 - Sa1) ** 2) / 2.)**0.5
    return FOS

def getResults(nodes):
    "Результати двох кроків для списку вузлів"
    res1=parseLines("    1PSTEP                         2           1           1")
    res2=parseLines("    1PSTEP                         6           1           2")
    res={}
    for node in nodes:
        SM_1=stressMises(*res1[node])
        S1_1,S2_1,S3_1=principalStress(*res1[node])
        SM_2=stressMises(*res2[node])
        S1_2,S2_2,S3_2=principalStress(*res2[node])
        fos=FOS(S1_2, S1_1, S2_2, S2_1, S3_2, S3_1)
        res[node]=[SM_1,SM_2,fos] # список потрібних результатів
    return res

def minFOSnode(res):
    "вузол з найменшим FOS. res - з getResults"
    minVal=1.e30
    for node in res:
        if res[node][2]<minVal:
            minVal=res[node][2]
            minNode=node
    with open('results.txt','w') as f:
        f.write(str(minVal))
    return minNode,minVal

if __name__=='__main__':
    res=parseLines("    1PSTEP                         2           1           1")
    node=1#res.keys()[0]
    print node,res[node]
    print stressMises(*res[node])
    print principalStress_(*res[node])
    print principalStress(*res[node])
    res=getResults([node])
    print minFOSnode(res)
    