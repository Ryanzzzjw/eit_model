


from typing import Any
import numpy as np
from eit_model.data import EITData
from eit_model.image import EITImage
import eit_model.setup
import eit_model.fwd_model
import eit_model.solver.solver_abc
import glob_utils.files.matlabfile
import glob_utils.args.check_type

## ======================================================================================================================================================
##  
## ======================================================================================================================================================


class EITModel(object):
    """ Class regrouping all information about the virtual model 
    of the measuremnet chamber used for the reconstruction:
    - chamber
    - mesh
    - 
    """
    name:str= 'EITModel_defaultName'


    def __init__(self):
        self.Name = 'EITModel_defaultName'
        # self.InjPattern = [[0,0], [0,0]]
        self.Amplitude= float(1)
        # self.meas_pattern=[[0,0], [0,0]]
        self.n_el=16
        self.p=0.5
        self.lamb=0.01
        self.n=64

        pattern='ad'
        # path= os.path.join(DEFAULT_DIR,DEFAULT_INJECTIONS[pattern])
        # self.InjPattern=np.loadtxt(path, dtype=int)
        # print(type(self.InjPattern))
        # path= os.path.join(DEFAULT_DIR,DEFAULT_MEASUREMENTS[pattern])
        # self.meas_pattern=np.loadtxt(path)
        # print(type(self.MeasPattern))
        # print(self.MeasPattern)
        self.SolverType= 'none'
        self.FEMRefinement=0.1
        # self.translate_inj_pattern_4_chip()

        self.setup= eit_model.setup.EITSetup()
        self.fwd_model=eit_model.fwd_model.FwdModel()
        self.fem= eit_model.fwd_model.FEModel()


    
    def set_solver(self, solver_type):
        self.SolverType= solver_type
    
    def import_matlab_env(self, var_dict):
        
        m= glob_utils.files.matlabfile.MatFileStruct()
        struct= m._extract_matfile(var_dict)

        fmdl= struct['fwd_model']
        fmdl['electrode']= eit_model.fwd_model.mk_list_from_struct(fmdl['electrode'], eit_model.fwd_model.Electrode)
        fmdl['stimulation']= eit_model.fwd_model.mk_list_from_struct(fmdl['stimulation'], eit_model.fwd_model.Stimulation)
        self.fwd_model= eit_model.fwd_model.FwdModel(**fmdl)

        setup= struct['setup']
        self.setup=eit_model.setup.EITSetup(**setup)

        self.fem= eit_model.fwd_model.FEModel(
            **self.fwd_model.for_FEModel(), **self.setup.for_FEModel())


    def translate_inj_pattern_4_chip(self, path=None):
        if path:
            self.ChipPins=np.loadtxt(path)
        else:
            # path= os.path.join(DEFAULT_DIR,DEFAULT_ELECTRODES_CHIP_RING)
            # self.ChipPins=np.loadtxt(path)
            """"""
        
        # test if load data are compatible...
        #todo..
        
        o_num=self.ChipPins[:,0] # Channel number
        n_num=self.ChipPins[:,1] # corresonpint chip pads
        new=np.array(self.InjPattern)
        old=np.array(self.InjPattern)
        for n in range(o_num.size):
            new[old==o_num[n]]= n_num[n]
            
        self.InjPattern= new # to list???
    
    @property    
    def refinement(self):
        return self.fem.refinement
    
    def set_refinement(self, value:float):
        glob_utils.args.check_type.isfloat(value,raise_error=True)
        if value >=1:
            raise ValueError('Value of FEM refinement have to be < 1.0')

        self.fem.refinement= value

    @property
    def n_elec(self, all:bool=True):
        return len(self.fem.electrode)

    # def set_n_elec(self,value:int):
        
    #     glob_utils.args.check_type.isint(value,raise_error=True)
    #     if value <=0:
    #         raise ValueError('Value of FEM refinement have to be > 0')
        
    #     self.setup.elec_layout.elecNb=value


    def pyeit_mesh(self, image:EITImage=None)->dict[str, np.ndarray]:
        """Return mesh needed for pyeit package

        mesh ={
            'node':np.ndarray shape(n_nodes, 2) for 2D , shape(n_nodes, 3) for 3D ,
            'element':np.ndarray shape(n_elems, 3) for 2D shape(n_elems, 4) for 3D,
            'perm':np.ndarray shape(n_elems,1),
        }

        Returns:
            dict: mesh dictionary
        """
        if image is not None and isinstance(image, EITImage):
            return {
                'node':image.fem['nodes'],
                'element':image.fem['elems'],
                'perm':image.data,
            }

        return self.fem.get_pyeit_mesh()

    def elec_pos(self)->np.ndarray:
        """Return the electrode positions 

            pos[i,:]= [posx, posy, posz]

        Returns:
            np.ndarray: array like of shape (n_elec, 3)
        """
        return self.fem.elec_pos_orient()[:,:3]

    def excitation_mat(self)->np.ndarray:
        """Return the excitaion matrix

           ex_mat[i,:]=[elec#IN, elec#OUT]

        Returns:
            np.ndarray: array like of shape (n_elec, 2)
        """
        return self.fwd_model.ex_mat()
    
    @property
    def meas_pattern(self)->np.ndarray:
        """Return the meas_pattern

            used to build the measurement vector
            measU = meas_pattern.dot(meas_ch)

        Returns:
            np.ndarray: array like of shape (n_measU, n_meas_ch*exitation)
        """
        return self.fwd_model.ex_mat()

    def build_img(self, data:np.ndarray=None, label:str='image')-> EITImage:
        
        data=self.fem.format_perm(data) if data is not None else self.fem.elems_data 
        fem={
            'nodes':self.fem.nodes,
            'elems':self.fem.elems,
            'elec_pos':self.fem.elec_pos_orient()
        }
        return EITImage(data, label, fem)
    
    def update_mesh(self, mesh_data:Any)->None:
        """Update FEM Mesh

        Args:
            mesh_data (Any): can be a mesh dict from Pyeit 
        """

        if isinstance(mesh_data, dict):
            self.fem.update_from_pyeit(mesh_data)

    def update_elec_from_pyeit(self,indx_elec:np.ndarray)->None:

        self.fem.update_elec_from_pyeit(indx_elec)
        

    def build_meas_data(self, ref:np.ndarray, frame:np.ndarray, label:str= '')->EITData:
        """"""
        #TODO  mk som test on the shape of the inputs
        meas= np.hstack((np.reshape(ref,(-1,1)), np.reshape(frame,(-1,1))))
        print(meas)
        return EITData(meas, label)
if __name__ == '__main__':

    import glob_utils.files.matlabfile
    import glob_utils.files.files

    file_path='E:/Software_dev/Matlab_datasets/20220307_093210_Dataset_name/Dataset_name_infos2py.mat'
    var_dict= glob_utils.files.files.load_mat(file_path)

    eit= EITModel()
    eit.import_matlab_env(var_dict)
    print(eit.fwd_model.electrode[1])
    print(eit.fwd_model.electrode[1])
    print(eit.refinement)

