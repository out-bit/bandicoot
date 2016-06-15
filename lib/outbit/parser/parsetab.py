
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.8'

_lr_method = 'LALR'

_lr_signature = '08D89100DBB39CDE1D5E28CD8ADD45C4'
    
_lr_action_items = {'OPTIONVALS':([8,],[13,]),'OPTIONVALD':([8,],[12,]),'SPACE':([1,3,5,6,7,10,11,12,13,14,],[-4,4,-6,-3,9,-7,-8,-10,-9,-5,]),'EQUAL':([6,15,],[8,8,]),'OPTIONVAL':([8,],[11,]),'ACTION':([0,4,8,9,],[1,6,10,15,]),'$end':([1,2,3,5,6,7,10,11,12,13,14,],[-4,0,-2,-6,-3,-1,-7,-8,-10,-9,-5,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'action_run':([0,],[2,]),'options':([4,],[7,]),'actions':([0,],[3,]),'option':([4,9,],[5,14,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> action_run","S'",1,None,None,None),
  ('action_run -> actions SPACE options','action_run',3,'p_action_run','yacc.py',16),
  ('action_run -> actions','action_run',1,'p_action_run','yacc.py',17),
  ('actions -> actions SPACE ACTION','actions',3,'p_actions','yacc.py',32),
  ('actions -> ACTION','actions',1,'p_actions','yacc.py',33),
  ('options -> options SPACE option','options',3,'p_options','yacc.py',48),
  ('options -> option','options',1,'p_options','yacc.py',49),
  ('option -> ACTION EQUAL ACTION','option',3,'p_option','yacc.py',61),
  ('option -> ACTION EQUAL OPTIONVAL','option',3,'p_option','yacc.py',62),
  ('option -> ACTION EQUAL OPTIONVALS','option',3,'p_option','yacc.py',63),
  ('option -> ACTION EQUAL OPTIONVALD','option',3,'p_option','yacc.py',64),
]
