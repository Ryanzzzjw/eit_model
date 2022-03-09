
from dataclasses import  dataclass, field
import numpy as np



@dataclass
class EITPattern():    
    """ define the overall dimensions of the chamber"""
    # _:KW_ONLY
    type:str= 'eit_pattern'
    injAmplitude:float= 1
    injType:str= '{ad}'
    injSpecial:str= '[1 2]'
    measType:str= '{ad}'
    measSpecial:str= '[1 2]'
    patternOption:list=field(default_factory=lambda:['meas_current'])
    patternFunc:str= 'Ring patterning'
    GENERATING_FUNCTIONS:list=field(default_factory=lambda:['Ring patterning',  'Array patterning',  '3D patterning'])
    PATTERNS:list=None
    
@dataclass
class EITElecLayout():
    # _:KW_ONLY
    type:str= 'eit_elec_layout'
    elecNb:int= 16
    elecForm:str= 'Circular'
    elecSize:np.ndarray=field(default_factory=lambda:np.array([0.5000, 0]))
    elecPlace:str= 'Wall'
    layoutDesign:str= 'Ring'
    layoutSize:float= 4
    zContact:float= 0.0100
    reset:int= 0
    ELEC_FORMS:list=field(default_factory=lambda:['Circular',  'Rectangular',  'Point'])
    LAYOUT_DESIGN:list=field(default_factory=lambda:['Ring',  'Array_Grid 0',  'Array_Grid 45'])
    ELEC_PLACE:list=field(default_factory=lambda:['Wall', 'Top',  'Bottom'])
    ALLOW_ELEC_PLACEMENT:np.ndarray=field(default_factory=lambda:np.array([]))

@dataclass
class EITChamber():
    # _:KW_ONLY
    type:str= 'eit_chamber'
    name:str='NameDesignOfChamber'
    boxSize:np.ndarray=field(default_factory=lambda:np.array([5, 5, 2]))
    femRefinement:float= 0.5000
    form:str= 'Cylinder'
    FORMS:list=field(default_factory=lambda:['Cylinder',  'Cubic',  '2D_Circ'])
    ALLOW_ELEC_PLACEMENT:np.ndarray=field(default_factory=lambda:np.array([]))


    def get_chamber_limit(self):
        x=self.length/2
        y=self.width/2
        z=self.height/2
        return [[-x,-y,-z],[x,y,z]] if z==0 else [[-x,-y],[x,y]]

    @property
    def length(self):
        return self.boxSize[0]
    @property
    def width(self):
        return self.boxSize[1]
    @property
    def height(self):
        return self.boxSize[2]

@dataclass
class EITSetup():
    type:str= 'eit_setup'
    chamber:EITChamber= EITChamber()
    elec_layout : EITElecLayout=EITElecLayout()
    pattern:EITPattern= EITPattern()

    def __post_init__(self):
        if isinstance(self.chamber, dict):
            self.chamber=EITChamber(**self.chamber)
        if isinstance(self.elec_layout, dict):
            self.elec_layout= EITElecLayout(**self.elec_layout)
        if isinstance(self.pattern, dict):
            self.pattern= EITPattern(**self.pattern)



    def for_FEModel(self) -> dict:

        return{'refinement': self.chamber.femRefinement}

if __name__ == '__main__':
    import glob_utils.files.matlabfile
    import glob_utils.files.files

    file_path='E:/Software_dev/Matlab_datasets/20220307_093210_Dataset_name/Dataset_name_infos2py.mat'
    var_dict= glob_utils.files.files.load_mat(file_path)
    m= glob_utils.files.matlabfile.MatFileStruct()
    struct= m._extract_matfile(var_dict)
    f= struct['setup']
    setup=EITSetup(**f)
    print(setup.__dict__)