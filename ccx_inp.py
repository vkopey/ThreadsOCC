# encoding: utf-8
"""Робота з файлами calculix .inp"""
import subprocess

filenameGmsh="gmsh.inp"
filename="model.inp"
nodes={} # вузли
lines={} # вузли ліній
elements={} # елементи поверхонь

# шаблон нижньої частини файла .inp    
_tmp="""
*MATERIAL, NAME=mat1
*ELASTIC
210000.0, 0.3
*MATERIAL, NAME=mat2
*ELASTIC
210000.0, 0.3 
*SOLID SECTION, ELSET=Surface1, MATERIAL=mat1
1.
*SOLID SECTION, ELSET=Surface2, MATERIAL=mat2
1.
*SOLID SECTION, ELSET=Surface3, MATERIAL=mat2
1.
{surfSlaveDefinitions}
{surfMasterDefinitions}
*SURFACE, NAME = surfBoltLoad, TYPE = ELEMENT
{surfBoltLoadDefinitions}
*PRE-TENSION SECTION, NODE={preTNode}, SURFACE=surfBoltLoad
0.0,1.0,0.0
*SURFACE INTERACTION, NAME=Int1
*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR
**1.e7, 3.
*CONTACT PAIR, INTERACTION=Int1, ADJUST=0.0, TYPE=SURFACE TO SURFACE
Slave, Master
*BOUNDARY
{boundLine1},1,2,0.0
*BOUNDARY
{boundLine2},1,1,0.0
*TIME POINTS,NAME=T1
1.0,2.0

*STEP
*STATIC
**1.e-4,1.
*BOUNDARY
{preTNode}, 1, 1, {boltLoad}
*NODE FILE, TIME POINTS=T1 
U,
*EL FILE, TIME POINTS=T1
S,
*CONTACT FILE, TIME POINTS=T1
CDIS, CSTR
*END STEP

*STEP
*STATIC
**1.e-4,1.
**CLOAD
**{loadLine1}, 2, 400.0
*DLOAD
{surfLoadDefinitions}
**CLOAD
**{preTNode}, 1, -4000.0
*BOUNDARY
{preTNode}, 1, 1, {boltLoad}
*NODE FILE, TIME POINTS=T1 
U,
*EL FILE, TIME POINTS=T1
S,
*CONTACT FILE, TIME POINTS=T1
CDIS, CSTR
*END STEP
"""

def mesh():
    """Створює сітку у Gmsh"""
    gmshPath=r"e:\Portable\gmsh-4.4.0-Windows64\gmsh.exe"
    subprocess.Popen("%s model.brep -2 -o gmsh.inp -format inp -order 2 -algo del2d -clscale 0.5 -clcurv"%gmshPath, shell=True).wait() # Gmsh->Abaqus
    
def runCCX():
    """Виконує розрахунок у ccx"""
    ccxPath=r"e:\CL33-win64\bin\ccx\ccx215.exe"
    s=subprocess.check_output([ccxPath, "-i", filename[:-4]], shell=True)
    L=[ln.strip() for ln in s.splitlines()[-10:]] # останні рядки виведення
    if "Job finished" in L:
        return 1 # якщо розрахунок успішний
    return 0
    
# додати заміну дуже малих чисел на 0?

def appendNode():
    """Додає у файл inp визначення нового вузла і повертає його номер"""
    f=readINP(filename) # прочитати рядки
    lns=[] # список нових рядків файла
    t='******* E L E M E N T S *************\n'
    prev="" # попередній рядок
    for ln in f: # для кожного рядка
        if ln==t: # якщо закінчилась секція вузлів
            lastNode=int(prev.split(',')[0].strip()) # номер останнього вузла
            # добавити визначення ще одного вузла
            lns.append(str(lastNode+1)+", 0, 0, 0\n")
        prev=ln
        lns.append(ln) 
    writeINP(lns) # зберегти рядки
    return lastNode+1
        
def elset2nset():
    """Конвертує файл gmsh.inp в CalculiX.inp
    аналогічно утіліти Prool's GMSH.inp to CCX.inp
    Увага! Застосовувати відразу після Gmsh"""
    f=readINP(filenameGmsh) # прочитати рядки
    lns=[] # список нових рядків файла
    t="" # поточна секція
    t1="*ELEMENT, type=T3D3, ELSET="
    t2="*NSET, NSET="
    nn=[] # вузли лінії
    for ln in f: # для кожного рядка
        # якщо заголовок секції *ELEMENT, type=T3D3, ELSET=
        if ln.startswith(t1):
            if nn: # якщо не перша секція
                # список вузлів і заголовок
                lnn="\n".join(nn)+"\n"+ln.replace(t1, t2)
            else: # якщо перша секція
                # тільки заголовок
                lnn=ln.replace(t1, t2)
            lns.append(lnn)
            t=t1 # позначити, що ми в середині секції
            nn=[] # очистити список вузлів
        # якщо в середині секції
        elif t==t1 and not ln.startswith("*ELEMENT"):
            ns=[x.strip() for x in ln.split(",")] # вузли
            if not nn: # якщо ми на початку секції
                nn+=ns[1:] # додати три вузла
            else: # якщо ми не на початку секції
                nn+=ns[2:] # додати два вузла
        # якщо секція закінчилась
        elif t==t1 and ln.startswith("*ELEMENT"):
            # список вузлів і заголовок
            lnn="\n".join(nn)+"\n"+ln
            lns.append(lnn)
            t="" # позначити, що ми поза секцією
            nn=[] # очистити список вузлів
        # якщо інші рядки
        else:    
            lns.append(ln) # залишаємо без змін
    writeINP(lns) # зберегти рядки       
     
def reverseOrient():
    """Змінює орієнтацію елементів у файлі .inp на протилежну.
    Нумерація вузлів елемента CAX6 змінюється так:
    1,2,3,4,5,6 -> 1,3,2,6,5,4
    Увага! Застосовувати після elset2nset(), якщо
    орієнтація елементів неправильна"""
    f=readINP() # прочитати рядки
    lns=[] # список нових рядків файла
    t="" # поточна секція
    t1="*ELEMENT, type=CPS6, ELSET="
    for ln in f: # для кожного рядка
        # якщо початок секції
        if ln.startswith(t1):
            t=t1
            lns.append(ln) # залишити без змін
        # якщо в секції
        elif t==t1 and ln.strip()[0] in "0123456789":
            el=[x.strip() for x in ln.split(",")]
            # змінити порядок вузлів
            eln=[el[0],el[1],el[3],el[2],el[6],el[5],el[4]]
            lnn=", ".join(eln)+"\n"
            lns.append(lnn)
        # якщо інші рядки
        else:
            t=""
            lns.append(ln) # залишити без змін    
    writeINP(lns) # зберегти рядки
    
def parse():
    """Парсер файлів calculix .inp
Увага! Застосовувати після elset2nset() і reverseOrient()"""
    f=readINP() # прочитати рядки
    t="" # поточна секція файлу inp
    t1="*NODE"
    t3="*NSET"
    t4="*ELEMENT"
    nset="" # назва лінії (множини вузлів)
    elset="" # назва поверхні (множини елементів)
    
    for ln in f: # для кожного рядка
        # парсимо в залежності від рядка ln і секції t
        # заголовок секції *NODE
        if ln.startswith(t1):
            t=t1
        # вузол
        elif t==t1 and ln.strip()[0] in "0123456789":
            ns=[e.strip() for e in ln.split(",")]
            nodes[int(ns[0])] = float(ns[1]), float(ns[2]), float(ns[3])
        # заголовок секції *NSET
        elif ln.startswith(t3):
            t=t3
            nset=ln.split("=")[1].strip()
            lines[nset]=[]
        # вузол лінії
        elif t==t3 and ln.strip()[0] in "0123456789":
            lines[nset].append(int(ln.strip()))
        # секція *Element
        elif ln.startswith(t4):
            t=t4
            elset=ln.split(",")[2].split("=")[1].strip()
            elements[elset]={}
        # вузли елемента
        elif t==t4 and ln.strip()[0] in "0123456789":
            es=[e.strip() for e in ln.split(",")]
            elements[elset][int(es[0])]=int(es[1]), int(es[2]), int(es[3]), int(es[4]), int(es[5]), int(es[6])

def findLine(x1,y1,x2,y2):
    """Шукає криву за двома точками"""
    r=11 # точність. Можна дати заоокруглення до r знаків, якщо не знаходить
    p=[round(x,r) for x in (x1,y1,x2,y2)] # заокруглити
    p1=p[0],p[1]
    p2=p[2],p[3]
    for ln in lines: # для кожної лінії
        ns=[nodes[x] for x in lines[ln]] # список вузлів на лінії
        nsr=[(round(n[0],r),round(n[1],r)) for n in ns] # заокруглити
        #if p1 in nsr and p2 in nsr: # якщо точки в списку <Тут не зовсім вірно. Див. нижче>
        # якщо крайні точки співпадають
        if p1==nsr[0] and p2==nsr[-1]:
            return ln
        if p2==nsr[0] and p1==nsr[-1]:
            return ln
    return None

def readINP(filename=filename):
    """Повертає рядки файлу .inp"""
    f=open(filename, 'r')
    ls=f.readlines()
    f.close()
    return ls

def writeINP(ls):
    """Записує рядки ls у файл .inp"""
    f=open(filename, 'w')
    f.writelines(ls)
    f.close()
    
def writeFinalINP(d):
    """Записує кінцевий файл .inp"""
    f=open(filename, 'r')
    s1=f.read()
    f.close()
    s1=replaceElType(s1)
    s2=_tmp.format(**d)
    f=open(filename, 'w')
    f.write(s1+s2)
    f.close()
    
def replaceElType(s):
    """Замінює тип елементів у тексті s"""
    old="*ELEMENT, type=CPS6, ELSET="
    new="*ELEMENT, type=CAX6, ELSET="
    return s.replace(old, new)

def partByElement(e):
    """Визначає деталь за елементом""" 
    for s in elements: # для кожної деталі
        if e in elements[s]: # якщо елемент серед елементів деталі
            return s # повертає назву деталі
    return None

def partByLine(ln):
    """Визначає деталь за лінією"""
    b=set(lines[ln]) # множина вузлів лінії
    for s in elements: # для кожної деталі
        a=set() # множина вузлів деталі
        for e in elements[s]: # для кожного елементу деталі
            ns=set(elements[s][e]) # множина вузлів елемента
            a.update(ns) #  додати до множини вузлів деталі 
        if b.issubset(a): # якщо вузли лінії серед вузлів деталі
            return s # повернути назву деталі
    return None

def findElementSurface(e):
    """Повертає назву лінії і назву сторони елемента на лінії.
    Тільки для елементів типу CAX6 !
    Наприклад, елемент CAX6 має вузли 1,2,3,4,5,6
    тоді сторони елемента нумеруються так:
    s1: 1-2, s2: 2-3, s3: 3-1"""
    s=partByElement(e) # назва деталі
    ns=elements[s][e] # вузли елемента
    for ln in lines: # для кожної лінії
        nsl=lines[ln] # вузли лінії
        nc=set(ns)&set(nsl) # множина спільних вузлів елемента і лінії
        if len(nc)==3: # якщо спільні три вузла (всього 6)
            s1=set(ns[:2])&nc
            s2=set(ns[1:3])&nc
            s3=set((ns[2],ns[0]))&nc
            # якщо обидва кутові вузли на лінії, то
            # повертає назву лінії і назву сторони елемента на лінії
            if len(s1)==2: return (ln,"S1")
            if len(s2)==2: return (ln,"S2")
            if len(s3)==2: return (ln,"S3")
    return (None,None)

def elementsByLine(ln,s=None):
    """Повертає список елементів лінії (код з surfByLineEl)"""
    res=[]
    if s==None: s=partByLine(ln) # назва деталі
    for e in elements[s]: # для кожного елемента деталі
        ls=findElementSurface(e)
        if ls[0]==ln: # якщо елемент на лінії
            res.append(e)
    return res

def surfByLineEl(ln,s=None):
    """Код визначення *SURFACE за елементами лінії"""
    surdef=""
    if s==None: s=partByLine(ln) # назва деталі
    
    for e in elements[s]: # для кожного елемента деталі
        ls=findElementSurface(e)
        if ls[0]==ln: # якщо елемент на лінії
            surdef+=str(e)+", "+str(ls[1])+"\n"
    return surdef
    
def dloadDefs(ln,s,value):
    _=surfByLineEl(ln,s)
    return _.replace('S','P').replace('\n',', %f\n'%value)
      
def surfDefs(lines,surfname):
    """Код визначення *SURFACE, які відповідають lines"""
    s="""*SURFACE, NAME = {name}, TYPE = ELEMENT\n""".format(name=surfname)
    for ln in lines:
        if ln: #!!!
            s+=surfByLineEl(ln)
    return s
    
def surfNodeDefs(lines,surfname):
    """Код визначення *SURFACE TYPE=NODE, які відповідають lines"""
    s="""*SURFACE, NAME = {name}, TYPE = NODE\n""".format(name=surfname)
    ls=[ln for ln in lines if ln]
    return s+',\n'.join(ls)
    
def findLines(pts):
    lns=[]
    for p1,p2 in pts:
        ln=findLine(x1=p1[0],y1=p1[1],x2=p2[0],y2=p2[1])
        lns.append(ln)
    return lns

def nodesByLines(lns):
    lnNodes=set()
    for ln in lns:
        if ln: lnNodes.update(lines[ln])
    return lnNodes
        
def nearestNode(x,y):
    mn=1e30
    for n in nodes:
        xn,yn,zn=nodes[n]
        d=((x-xn)**2+(y-yn)**2)**0.5
        if d<mn:
            mn=d
            nnode=n
    return nnode,mn
        
if __name__=='__main__':
    print "ccx_inp"
    elset2nset()
    #reverseOrient()
    parse()
    print nearestNode(11.13, 23.87)

    # for n in nodes:
    #     print n, nodes[n]

    # for n in lines:
    #     print n, lines[n]

    # for n in lines:
    #     print n, [nodes[x] for x in lines[n]]

    # for s in elements:
    #     print s
    #     for e in elements[s]:
    #         #print e,elements[s][e]
    #         print findElementSurface(e)

    # print findLine(0,0,0.8864911064067351,0)
    # 
    # print surfByLineEl("Line1")
    # 
    # print surfsDefs(["Line1","Line2","Line3"])

    # for e in elements['Surface2']:
    #     print partByElement(e)

    # print partByLine("Line1")