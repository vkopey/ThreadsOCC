# encoding: utf-8
import subprocess

filenameGmsh="my.inp"
filename="model.inp"

# шаблон нижньої частини файла .inp    
_tmp="""
*MATERIAL, NAME=mat1
*ELASTIC
210000.0, 0.3
*SOLID SECTION, ELSET=Surface1, MATERIAL=mat1
1.
*BOUNDARY
{boundLine1},1,2,0.0

*STEP
*STATIC
*BOUNDARY
{loadLine1},2,2,0.01
*EL PRINT, ELSET=Surface1
S
*NODE FILE
U,
*EL FILE
S,
*END STEP
"""

def mesh():
    """Створює сітку у Gmsh"""
    gmshPath="e:\\Portable\\gmsh-4.13.1-Windows64\\gmsh.exe"
    subprocess.Popen("%s - -v 0 my.geo"%gmshPath, shell=True).wait() # Gmsh->Abaqus
    
def runCCX():
    """Виконує розрахунок у ccx"""
    ccxPath=r"d:\\Portable\\cae_20200725_windows\\bin\\ccx.exe"
    s=subprocess.check_output([ccxPath, "-i", filename[:-4]], shell=True)
    L=[ln.strip() for ln in s.splitlines()[-10:]] # останні рядки виведення
    if "Job finished" in L:
        return 1 # якщо розрахунок успішний
    return 0
        
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


if __name__=='__main__':
    elset2nset()
    d={"boundLine1":"Line31","loadLine1":"Line26"}
    writeFinalINP(d)
    runCCX()
    