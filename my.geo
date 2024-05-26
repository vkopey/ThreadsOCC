// Gmsh project created on Sun May 26 13:33:54 2024
SetFactory("OpenCASCADE");
//+
Rectangle(1) = {0, 0.05, 0, 1, 1.8, 0};

p=0.0;
For t In {1:5}
  x=4*t;
  Point(1+x) = {0.5, 0.0+p, 0, 1.0};
  Point(2+x) = {0.4, 0.1+p, 0, 1.0};
  Point(3+x) = {0.6, 0.3+p, 0, 1.0};
  Point(4+x) = {0.7, 0.2+p, 0, 1.0};

  Line(1+x) = {1+x, 2+x};
  Line(2+x) = {2+x, 3+x};
  Line(3+x) = {3+x, 4+x};
  Line(4+x) = {4+x, 1+x};

  Curve Loop(1+t) = {1+x, 2+x, 3+x, 4+x};
  Plane Surface(1+t) = {1+t};
  //BooleanDifference{ Surface{1};}{ Surface{1+t};}

  p += 0.4;
EndFor

BooleanDifference{ Surface{1}; Delete; }{ Surface{2}; Surface{3}; Surface{4}; Surface{5}; Surface{6}; Delete; };
//Physical Curve("Encastr", 35) = {31};
//Physical Curve("Loading", 36) = {26};
Mesh.ElementOrder = 2;
Mesh 2;
Mesh.SaveAll=1;
Save "my.inp";
