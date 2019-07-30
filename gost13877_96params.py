# -*- coding: utf-8 -*-
from math import *
steel45={'el':((210000000000.0, 0.28), ),
               'pl':((620000000.0, 0.0),
                     (640000000.0, 0.02),
                     (800000000.0, 0.04),
                     (860000000.0, 0.08),
                     (864000000.0, 0.11))}
##
class Dim:
    "Клас описує поняття розміру"
    n=0.0 #номінальний розмір
    ei=0.0 #нижнє відхилення
    es=0.0 #верхнє відхилення
    v=0.0 #дійсне значення
    def __init__(self,n=None,ei=None,es=None,doc=""):
        self.n=n
        self.ei=ei
        self.es=es
        self.__doc__=doc.decode('utf-8')

    def min(self):
        "повертає мінімальний розмір"
        return self.n+self.ei
        
    def max(self):
        "повертає максимальний розмір"
        return self.n+self.es
##        
class Rod(object):
    d_n=Dim(doc="зовнішній діаметр різьби")
    d2_n=Dim(doc="середній діаметр різьби")
    d1_n=Dim(doc="внутрішній діаметр різьби")
    r_n=Dim(doc="радіус западин різьби")
    dn=Dim(doc="діаметр бурта")
    d1n=Dim(doc="діаметр зарізьбової канавки")
    l1n=Dim(doc="довжина ніпеля")
    l2n=Dim(doc="довжина зарізьбової канавки")
    l3n=Dim(doc="довжина ніпеля без фаски на різьбі")
    l4n=Dim(doc="довжина ніпеля з буртом")
    r3n=Dim(doc="радіус скруглень зарізьбової канавки")
    d_m=Dim(doc="зовнішній діаметр різьби")
    d2_m=Dim(doc="середній діаметр різьби")
    d1_m=Dim(doc="внутрішній діаметр різьби")
    dm=Dim(doc="зовнішній діаметр")
    d1m=Dim(doc="внутрішній діаметр опорної поверхні")
    lm=Dim(doc="довжина муфти")
    d0=Dim(doc="діаметр тіла")
    p_n=Dim(doc="крок різьби")
    p_m=Dim(doc="крок різьби")

    def setModelParams(self,**args):
        self.l_=0 #скорочення муфти при згвинчуванні (0, якщо задано Bolt Load)
        #=====================параметри ніпеля штанги===================
        self.d_n = self.d_n.min() / 2 #зовнішній діаметр різьби/2
        self.d2_n = self.d2_n.min() / 2 #середній діаметр різьби/2
        self.d1_n = self.d1_n.min() / 2 #внутрішній діаметр різьби/2!ei*
        self.r_n = self.r_n.min() #радіус западин різьби
        self.p_n = self.p_n.min() #крок різьби
        self.dn = self.dn.min() / 2 #діаметр бурта/2
        self.d1n = self.d1n.min() / 2 #діаметр зарізьбової канавки/2
        self.l1n = self.l1n.min() #довжина ніпеля
        self.l2n = self.l2n.min() #довжина зарізьбової канавки
        self.l3n = self.l3n.min() #довжина ніпеля без фаски на різьбі
        self.l4n = self.l4n.min() #довжина ніпеля з буртом
        self.r3n = self.r3n.min() #радіус скруглень зарізьбової канавки
        self.d0 = self.d0.min() / 2 #діаметр тіла/2
        #=====================параметри муфти===========================
        self.d_m = self.d_m.max() / 2 #зовнішній діаметр різьби/2!es*
        self.d2_m = self.d2_m.max() / 2 #середній діаметр різьби/2
        self.d1_m = self.d1_m.max() / 2 #внутрішній діаметр різьби/2
        self.p_m = self.p_m.min() #крок різьби
        self.dm = self.dm.min() / 2 #зовнішній діаметр/2
        self.d1m = self.d1m.max() / 2 #внутрішній діаметр опорної поверхні/2
        self.lm = self.lm.min() / 2 #довжина муфти/2
        
        for k in args:
            self.__dict__[k]=args[k]
            
        #================допоміжні параметри========================
        self.dn_=self.d2_n+0.25*self.p_n/tan(30*pi/180) #зовнішній діаметр вершин трикутника профіля ніпеля
        self.ln_=self.l1n-self.l2n #z-координата першої западини ніпеля (довжина різьби ніпеля)
        self.dm_=self.d2_m-0.25*self.p_m/tan(30*pi/180) #внутрішній діаметр вершин трикутника профіля муфти
        self.lm_=self.lm-11.1 #довжина різьби муфти
        self.l2m_=self.ln_+ceil((self.l2n-11.1)/self.p_m)*self.p_m-3*self.p_m/2-(self.d2_m-self.d2_n)*tan(30*pi/180) #z-координата першої западини муфти
        #ceil((self.l2n-11.1)/self.p_m)*self.p_m - перші неробочі витки муфти
        #-3*self.p_m/2-(self.d2_m-self.d2_n)*tan(30*pi/180) - зміщення профілю муфти
        #===============точки характерних кромок моделі==================
        self.en1=(self.dn/2, self.l4n, 0.0) #верхній торець штанги (було l1n+20)
        self.en2=(0.0, self.l4n/2, 0.0) #вісь ніпеля
        self.en3=(self.d1_n/2,0.0,0.0) #нижній торець штанги
        self.en4=(self.dn,self.l4n-5,0.0) #зовнішній циліндр бурта
        self.enr1=(self.d2_n-0.25*self.p_n/tan(30*pi/180)+self.r_n/sin(30*pi/180)-self.r_n,self.ln_,0.0) #центр першої западини ніпеля
        self.em1=((self.dm+self.d_m)/2, self.l1n-self.lm+self.l_, 0.0) #нижній торець муфти (зміщення +self.l_)
        self.em2=(self.dm,self.l1n/2,0.0) #зовнішній циліндр муфти
        self.em3=((self.dm+self.d1m)/2,self.l1n-5,0.) #центр Partition face-1 (для Bolt Load)
        self.em4=((self.dm+self.d1m)/2,self.l1n,0.) #верхній торець муфти
        self.nn=8 #кількість западин ніпеля для дослідження
        self.mat1=steel45 # матеріал 1
        self.mat2=steel45 # матеріал 2
        self.bolt_load=-0.1
        self.load1=-1*self.d0/self.dn
        self.load2=-155.1*self.d0/self.dn #-276.0*self.d0/self.dn 

##
class Rod19(Rod):    
    d_n=Dim(27, -0.48, -0.376)
    d2_n=Dim(25.35, -0.204, -0.047)
    d1_n=Dim(24.25, 0, -0.415)
    r_n=Dim(0.28, 0, 0.08)
    dn=Dim(38.1, -0.25, 0.13)
    d1n=Dim(23.24, -0.13, 0.13)
    l1n=Dim(36.5, 0, 1.6)
    l2n=Dim(15, 0.2, 1)
    l3n=Dim(32, 0, 1.5)
    l4n=Dim(48, -1, 1.5)
    r3n=Dim(3, 0, 0.8)
    d_m=Dim(27, 0, 0.27)
    d2_m=Dim(25.35, 0, 0.202)
    d1_m=Dim(24.25, 0, 0.54)
    dm=Dim(41.3, -0.25, 0.13)
    d1m=Dim(27.43, 0, 0.25)
    lm=Dim(102, -1, 1)
    d0=Dim(19.1,-0.41,0.2)
    p_n=Dim(2.54,0,0)
    p_m=Dim(2.54,0,0)
    def __init__(self,**args):
        for k in Rod19.__dict__:
            if Rod19.__dict__[k].__class__==Dim:
               Rod19.__dict__[k].__doc__=Rod.__dict__[k].__doc__ # атрибут документації
        self.setModelParams(**args)
        
    
if __name__=="__main__":
    r=Rod19()
    #r.setModelParams()
    r.dn_
