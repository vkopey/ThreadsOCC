#-*- coding: utf-8 -*-
#from __future__ import unicode_literals
import math,sys
from myBaseGeom import *
# Засоби для створення простого GUI
# розкоментувати, якщо потрібна візуалізація
#from OCC.Display.SimpleGui import init_display
#display, start_display, add_menu, add_function_to_menu = init_display()
#display.set_bg_gradient_color(255,255,255,255,255,255) # колір фону

from OCC.BRepBuilderAPI import *
from OCC.TopoDS import *
from OCC.TopExp import *
from OCC.TopAbs import *
from OCC.BRepFilletAPI import BRepFilletAPI_MakeFillet2d
from OCC.ChFi2d import ChFi2d_ChamferAPI,ChFi2d_FilletAPI
from OCC.BRep import BRep_Tool_Pnt
from OCC.BRepAlgoAPI import *
from OCC.BRepAlgo import *
# замість BRepAlgoAPI_Fuse використовувати BRepAlgo_Fuse, щоб результатом була одна грань
from OCC.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCC.Precision import precision_Confusion

from gost13877_96params import Rod19
#параметри можуть передаватись через командний рядок:
d={}
for i in sys.argv[1:]: exec i in None,d
d=Rod19(**d)
#d=Rod19(r3n=2.5)
#d=Rod19(d_n=13.12)#12.7,12.84,12.98,13.12,13.26    

def translate(f,x1,y1,x2,y2):
    u"""Переміщення з точки в точку"""
    #gp_Trsf2d
    trsf=gp_Trsf()
    trsf.SetTranslation(gp_Pnt(x1,y1,0),gp_Pnt(x2,y2,0)) # переміщення
    f=BRepBuilderAPI_Transform(f,trsf).Shape()
    return f

def rotate(f, angle):
    u"""Поворот навколо осі z на кут angle"""
    trsf=gp_Trsf() # трансформація
    trsf.SetRotation(gp_Ax1(),angle) # поворот
    f=BRepBuilderAPI_Transform(f,trsf).Shape()
    return f         

def poly(pts):
    u"""Полігон зі скругленнями і фасками
    Приклад:
    poly(pts=[[(0,0),1],[(10,0),(1,1)],[(5,5),None]])
    тут 1 - радіус скруглення біля вершини,
    (1,1) - фаска біля вершини,
    None або 0 - без фаски чи скруглення біля вершини"""
    gpts=[gp_Pnt(p[0][0],p[0][1],0) for p in pts] # точки вершин
    es=[] # список ребер (без фасок і скруглень)
    p1=gpts[-1] # остання точка
    for p2 in gpts: # для кожної точки
        e=BRepBuilderAPI_MakeEdge(p1,p2).Edge() # створити ребро
        es.append(e) # додати у список
        p1=p2 # попередня точка
        
    ecs=[] # список містить ребра фаски чи скруглення або None
    for i,p in enumerate(pts): # для кожної точки
        if i==len(pts)-1: j=0 # індекс другого ребра
        else: j=i+1
        pcf=p[1] # розміри фаски чи скруглення
        if type(pcf) in [tuple,list]: # якщо фаска
            ch=ChFi2d_ChamferAPI(es[i],es[j]) # фаска за двома ребрами
            ch.Perform()
            ec=ch.Result(es[i],es[j],pcf[0],pcf[1]) # ребро фаски
            # es[i],es[j] - нові ребра біля фаски
        elif not pcf: # без фаски чи скруглення
            ec=None
        else: # скруглення
            fl=ChFi2d_FilletAPI(es[i],es[j],gp_Pln()) # скруглення за двома ребрами
            fl.Perform(pcf)
            ec=fl.Result(gpts[i],es[i],es[j]) # ребро скруглення
            # es[i],es[j] - нові ребра біля скруглення
        ecs.append(ec) # додати ребро фаски чи скруглення у список
    en=[] # список усіх остаточних ребер
    for e,ec in zip(es,ecs):
        en.append(e) # додати ребро
        if ec: en.append(ec) # додати ребро фаски чи скруглення, якшо не None 
       
#     # ще один спосіб створення полігону
#     mp = BRepBuilderAPI_MakePolygon()
#     for p in gpts:
#         mp.Add(p)
#     mp.Close()
#     w=mp.Wire()

    mw=BRepBuilderAPI_MakeWire() # створити контур
    for e in en: # для кожного ребра
        mw.Add(e) # додати в контур
    w=mw.Wire() # контур
    f=BRepBuilderAPI_MakeFace(w).Face() # грань

#     # ще один спосіб створення скруглень       
#     mf=BRepFilletAPI_MakeFillet2d(f)
#     ex = TopExp_Explorer(f, TopAbs_VERTEX)
#     hasFillet=False 
#     while ex.More():
#         v = topods_Vertex(ex.Current())
#         vp=BRep_Tool_Pnt(v)
#         if v.Orientation()==TopAbs_FORWARD:
#             for i in range(len(gpts)):
#                 if vp.IsEqual(gpts[i],1e-6) and r[i]!=0:
#                     print vp.X(),vp.Y(),vp.Z()
#                     hasFillet=True
#                     mf.AddFillet(v,r[i])
#         ex.Next()
#         
#     if hasFillet: f=mf.Shape()
    
    return f

def rect(Lx,Ly,c=[0,0,0,0]):
    u"""Прямокутник з першим кутом (нижній лівий) в 0,0
    c - фаски чи скруглення кутів"""
    pts=[[(0,0),c[0]],[(Lx,0),c[1]],[(Lx,Ly),c[2]],[(0,Ly),c[3]]]
    return poly(pts)
    
def cut_array(f1,f2,ps):
    u"""Робить масив вирізів поверхнею f1 у поверхні f2.
    Список точок вирізів ps=[(0,0),(0,1),(0,2)]"""
    p0=ps[0]
    for p in ps[1:]:
        f2=BRepAlgoAPI_Cut(f2, f1).Shape()
        f1=translate(f1,p0[0],p0[1],p[0],p[1])
        p0=p
    f2=BRepAlgoAPI_Cut(f2, f1).Shape()
    return f2

def thread_points_array(p0,L,s):
    u"""Масив точок для побудови різьби довжиною L та кроком s. Крок може бути відємний. p0 - початкова точка"""
    ps=[] 
    y=p0[1]
    l=0 # поточна довжина різьби
    while l<=L:
        ps.append((p0[0],y))
        y+=s
        l+=abs(s)
    return ps  
    
def face1():
    u"""Ніпель"""
    h=d.l1n-d.l3n # фаска ніпеля
    f1=rect(d.d_n, d.l1n, [0,(0.577*h,h),0,0]) # ніпель
    f2=rect(d.dn, d.l4n-d.l1n, [0,0,0,0]) # бурт
    f2=translate(f2, 0, 0, 0, d.l1n)
    f3=BRepAlgo_Fuse(f2, f1).Shape()
    
    f41=rect(d.dn, d.l2n, [0,0,0,0]) # заготовка канавки
    f41=translate(f41, 0, 0, 0, d.l1n-d.l2n)
    f3=BRepAlgo_Fuse(f3, f41).Shape()
    
    f4=rect(d.dn-d.d1n, d.l2n, [d.r3n,0,0,d.r3n]) # виріз канавки
    f4=translate(f4, 0, 0, d.d1n, d.l1n-d.l2n)
    f5=BRepAlgoAPI_Cut(f3, f4).Shape()
    
    tn1=math.tan(math.radians(30)) # tan верхнього кута профілю
    tn2=math.tan(math.radians(30)) # tan нижнього кута профілю
    H=2.2 # висота різця
    f6=poly([[(0,0),d.r_n],[(H,-H*tn2),0],[(H,H*tn1),0]]) # різець
    f6=translate(f6, 0, 0, -H, 0)
    #display.DisplayShape(f6,update=True,color='red')
    
    f6=translate(f6, 0, 0, d.dn_, d.ln_)
    a=thread_points_array((d.dn_,d.ln_), d.l1n-d.l2n, -d.p_n)
    f=cut_array(f6,f5,a) # ніпель з різьбою
    
    #print f.ShapeType() # COMPOUND
    # отримати поверхню
    ex = TopExp_Explorer(f, TopAbs_SHELL)
    f=topods_Shell(ex.Current())
    return f

def face2():
    u"""Муфта"""
    f1=rect(d.dm-d.d1m, d.lm, [0,0,(3,0.8),(1.15,2)]) # муфта
    f1=translate(f1,0,0,d.d1m,-(d.lm-d.l1n))
    h=d.d1m-d.d1_m # фаска
    f2=rect(d.dm-d.d1_m, d.lm-10, [0,0,0,(h,1.73*h)]) # заготовка різьбової частини
    f2=translate(f2, 0, 0, d.d1_m, -(d.lm-d.l1n))
    f2=BRepAlgo_Fuse(f2, f1).Shape()
    
    tn1=math.tan(math.radians(30)) # tan верхнього кута профілю
    tn2=math.tan(math.radians(30)) # tan нижнього кута профілю
    H=2.2 # висота різця
    #f3=poly([[(0,0),0],[(0.3,-0.1),0],[(0.3,-0.11),0],[(0,-0.21),0]])
    f3=poly([[(0,H*tn1),0],[(H,0),(0.275/0.866, 0.275/0.866)],[(0,-H*tn2),0]]) # різець
    #display.DisplayShape(f3,update=True,color='red')
    
    f3=translate(f3, 0, 0, d.dm_, d.l2m_)    
    a=thread_points_array((d.dm_, d.l2m_), d.lm_, -d.p_m)
    f=cut_array(f3,f2,a) # муфта з різьбою
    
    #print f.ShapeType() # COMPOUND !!!
    # ребро для поділу грані на дві частини
    e1=BRepBuilderAPI_MakeEdge(gp_Pnt(d.d1m,d.l1n-5,0),gp_Pnt(d.dm,d.l1n-5,0)).Edge()
    
    # отримати грань
    ex = TopExp_Explorer(f, TopAbs_FACE)
    ff=topods_Face(ex.Current())
    
    # розділити грань ребром
    from OCC.BRepFeat import BRepFeat_SplitShape
    ss=BRepFeat_SplitShape(f)
    ss.Add(e1,ff)
    f=ss.Shape()
    #print f.ShapeType() # COMPOUND
    
    # отримати поверхню
    ex = TopExp_Explorer(f, TopAbs_SHELL)
    f=topods_Shell(ex.Current())
    
    return f

def mkCompaund(f1,f2):
    u"""Об'єднує форми для експорту в формат BRep"""
    from OCC.BRep import BRep_Builder
    f=TopoDS_Compound()
    bb=BRep_Builder()
    bb.MakeCompound(f)
    bb.Add(f,f1)
    bb.Add(f,f2)
    return f

def findContEdges(f, exPoints):
    u"Шукає усі ребра грані f крім тих, що задані exPoints. Для контактних задач. Повертає список ребер у вигляді крайніх точок p1,p2"
    ex = TopExp_Explorer(f, TopAbs_EDGE) # переглядач ребер
    edges=[] # ребра не для контакту як їх крайні точки
    edgesc=[] # ребра для контакту як їх крайні точки
    for p in exPoints:
        x,y=p[1]
        edges.append(findEdge(f,x,y))
    while ex.More():
        e = topods_Edge(ex.Current()) # поточне ребро
        ps=edgeBoundPts(e)
        if (ps[0][0],ps[0][1],ps[1][0],ps[1][1]) not in edges:
            edgesc.append(ps)
        ex.Next()
    return edgesc

def edgeBoundPts(e):
    u"""Повертає крайні точки ребра"""
    v1=topexp_FirstVertex(e) # перша вершина ребра
    p1=BRep_Tool_Pnt(v1) # точка за вершиною
    v2=topexp_LastVertex(e) # остання вершина ребра
    p2=BRep_Tool_Pnt(v2) # точка за вершиною
    return ((p1.X(),p1.Y()),(p2.X(),p2.Y()))       

def drawEdgePts(e):
    u"Рисує крайні точки ребра"
    x1,y1,x2,y2=e
    display.DisplayShape(gp_Pnt(x1,y1,0), color='black')
    display.DisplayShape(gp_Pnt(x2,y2,0), color='black')

def findEdge(f,x,y):
    u"""Шукає ребро поверхні f за точкою на ньому
    Повертає кортеж першої і останньої точок ребер:
    x1,y1,x2,y2"""
    from OCC.BRep import BRep_Tool_Curve
    from OCC.GeomAdaptor import GeomAdaptor_Curve
    from OCC.GeomLib import GeomLib_Tool_Parameter
    px=gp_Pnt(x,y,0)
    #display.DisplayShape(px, color='black')
    ex = TopExp_Explorer(f, TopAbs_EDGE) # перглядач ребер
    while ex.More():
        e = topods_Edge(ex.Current()) # поточне ребро
        c=BRep_Tool_Curve(e) #! зверніть увагу, що результат є кортежом
        gac=GeomAdaptor_Curve(c[0],c[1],c[2]) # крива (OCC.Geom.Handle_Geom_Curve), перший параметр, другий параметр
        
        #tp=gac.GetType() # тип кривої 0 - лінія, 1 - коло, ...
        #print type(gac.Line()) # OCC.gp.gp_Lin
        #p = gp_Pnt()
        #gac.D0((c[1]+c[2])/2.0, p) # p - середня точка кривої
        #display.DisplayShape(p, color='black')
        #gac.Line().Contains(px,1e-9) # чи лінія містить точку
        
        res=GeomLib_Tool_Parameter(c[0],px,1e-9) # ! зверніть увагу, що
        # результат є кортежом. Це не відповідає документації.
        if res[0] and res[1]>=c[1] and res[1]<=c[2]: # якщо точка на кривій в заданих межах параметрів
            p1=gac.Value(c[1]) # перша точка кривої
            p2=gac.Value(c[2]) # остання точка кривої
            #display.DisplayShape(p1, color='black')
            #display.DisplayShape(p2, color='black')
            return p1.X(),p1.Y(),p2.X(),p2.Y()
        ex.Next()
    return None

##IsVertexOnLine
##ComputePE
##VertexParameter        

def findEdge2(f,x,y):
    u"""Шукає ребро поверхні f за точкою на ньому"""
    from OCC.BRepExtrema import BRepExtrema_ExtPC
    vx=BRepBuilderAPI_MakeVertex(gp_Pnt(x, y, 0)).Vertex() # вершина
    #display.DisplayShape(vx, color='black')
    extr=BRepExtrema_ExtPC() # знаходить відстані від вершини до ребра
    ex = TopExp_Explorer(f, TopAbs_EDGE) # перглядач ребер
    while ex.More(): # для кожного ребра
        e = topods_Edge(ex.Current()) # поточне ребро
        extr.Initialize(e)
        extr.Perform(vx)
        if extr.IsDone(): # якщо екстремуми знайдені
            for i in range(1,extr.NbExt()+1): # для кожного екстремума
                if extr.SquareDistance(i)<1e-6: # квадрат відстані до першого екстремуму
                    p=edgeBoundPts(e)
                    return p[0][0],p[0][1],p[1][0],p[1][1]
        ex.Next()
    return None

def drawMesh(es):
    u"""Рисує сітку елементів es"""
    for e in es: # для кожного елемента
        for s in ccx_inp.elements: # для кожної деталі
            # якщо елемент не цієї деталі, то пропустити
            if not e in ccx_inp.elements[s]: continue
            ns=ccx_inp.elements[s][e] # вузли елемента
            ps=[] # точки gp_Pnt
            for n in ns: # для кожного вузла
                x,y,z=ccx_inp.nodes[n] # координати вузла
                ps.append(gp_Pnt(x,y,z)) # додати точку
                display.DisplayShape(ps[-1]) # показати точку
                display.DisplayMessage(ps[-1],str(n),message_color=(0,0,0))
            poly=BRepBuilderAPI_MakePolygon(ps[0],ps[1],ps[2],True).Shape()
            display.DisplayShape(poly) # показати полігон елемента

def visualize(shape):
    u"""Налаштовує параметри візуалізації і показує форму"""
    #from OCC.Display.OCCViewer import Viewer3d
    display.View_Top()
    display.set_bg_gradient_color(255,255,255,255,255,255)
    # сітка
    for x in range(0,50,10):
        for y in range(0,50,10):
            #for z in range(3):
            display.DisplayShape(gp_Pnt(x,y,0)) 
    display.DisplayShape(shape,update=True)

def saveBrep(shape,filename):
    u"""Зберегти форму у форматі BRep"""
    from OCC.BRepTools import breptools_Write # функція PythonOCC для запису BRep
    breptools_Write(shape,filename) # зберегти в PythonOCC у форматі BRep

###########################################################

f1=face1() # ніпель
f2=face2() # муфта
f=mkCompaund(f1,f2)
saveBrep(f,"model.brep")
#visualize(f) # візуалізація форми

p={} # словник характерних точок моделі
p[1]=[f2, d.em1[:2]] # нижній торець муфти
p[2]=[f1, d.en1[:2]] # верхній торець ніпеля
p[3]=[f1, d.em4[:2]] # точка на контактній поверхні бурта
p[4]=[f2, d.em4[:2]] # точка на контактній поверхні бурта
p[5]=[f1, d.en2[:2]] # вісь ніпеля
p[6]=[f2, d.em3[:2]] # лінія поділу муфти
p[7]=[f1, d.en3[:2]] # нижній торець ніпеля
p[8]=[f1, d.en4[:2]] # зовнішній циліндр бурта
p[9]=[f2, d.em2[:2]] # #зовнішній циліндр муфти

import ccx_inp
ccx_inp.mesh()
ccx_inp.elset2nset()
lastNode=ccx_inp.appendNode()
#ccx_inp.reverseOrient()
ccx_inp.parse()
 
def linFinder():
    """Додадає лінії у словник характерних точок"""
    for i in p:
        e=findEdge(p[i][0],*p[i][1])
        p[i].append(ccx_inp.findLine(*e))
linFinder()
#print p[6][2] # назва лінії
#drawEdgePts(findEdge(f2,*p[9][1]))

ce1=findContEdges(f=f1, exPoints=[p[7], p[5], p[2], p[8]])
ce2=findContEdges(f=f2, exPoints=[p[9], p[1], p[6]])
master=ccx_inp.findLines(ce1)
#print master # !warning some None
slave=ccx_inp.findLines(ce2)
print len(master), len(set(master)) # чомусь не рівні?
print len(slave), len(set(slave))

c={}
c["surfSlaveDefinitions"]=ccx_inp.surfDefs(set(slave),"Slave")
#c["surfSlaveDefinitions"]=ccx_inp.surfNodeDefs(set(slave),"Slave")
c["surfMasterDefinitions"]=ccx_inp.surfDefs(set(master),"Master")
c["surfBoltLoadDefinitions"]=ccx_inp.surfByLineEl(p[6][2],"Surface3")
c["surfLoadDefinitions"]=ccx_inp.dloadDefs(p[2][2],"Surface1",d.load2)
c["boundLine1"]=p[1][2]
c["loadLine1"]=p[2][2]
c["boundLine2"]=p[5][2]
c["preTNode"]=lastNode
c["boltLoad"]=d.bolt_load

ccx_inp.writeFinalINP(c)
if not ccx_inp.runCCX(): print "ccx error"
import ccx_out
res=ccx_out.getResults(ccx_inp.nodesByLines(master))
print "FOS=",ccx_out.minFOSnode(res)[1] #мінімальні FOS на поверхні ніпеля
res=ccx_out.getResults(ccx_inp.nodesByLines([p[4][2]]))
print sum([res[n][1] for n in res])/len(res) # середні напруження на бурті на другому кроці
 
"""
# візуалізація елементів
lnels=set() # множина елементів на контактних лініях
for ln in slave+master:
    if not ln: continue
    lnels.update(set(ccx_inp.elementsByLine(ln)))
#та на лінії BoltLoad
lnels.update(set(ccx_inp.elementsByLine(p[6][2],"Surface2")))
#та на лінії навантаження
lnels.update(set(ccx_inp.elementsByLine(p[2][2],"Surface1")))
drawMesh(lnels)
#drawMesh(ccx_inp.elements['Surface1'])
"""
#start_display()
