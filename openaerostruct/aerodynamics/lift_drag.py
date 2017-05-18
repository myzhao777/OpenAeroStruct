from __future__ import print_function, division
import numpy as np

from openmdao.api import ExplicitComponent

try:
    import OAS_API
    fortran_flag = True
    data_type = float
except:
    fortran_flag = False
    data_type = complex

class LiftDrag(ExplicitComponent):
    """
    Calculate total lift and drag in force units based on section forces.
    This is for one given lifting surface.

    inputeters
    ----------
    sec_forces[nx-1, ny-1, 3] : numpy array
        Flattened array containing the sectional forces acting on each panel.
        Stored in Fortran order (only relevant with more than one chordwise
        panel).
    alpha : float
        Angle of attack in degrees.

    Returns
    -------
    L : float
        Total induced lift force for the lifting surface.
    D : float
        Total induced drag force for the lifting surface.

    """

    def initialize(self):
        self.metadata.declare('surface', type_=dict)

    def initialize_variables(self):
        self.surface = surface = self.metadata['surface']

        ny = surface['num_y']
        nx = surface['num_x']
        self.num_panels = (nx - 1) * (ny - 1)

        self.add_input('sec_forces', val=np.zeros((nx-1, ny-1, 3)))
        self.add_input('alpha', val=3.)
        self.add_output('L', val=0.)
        self.add_output('D', val=0.)

    def compute(self, inputs, outputs):
        alpha = inputs['alpha'] * np.pi / 180.
        forces = inputs['sec_forces'].reshape(-1, 3)
        cosa = np.cos(alpha)
        sina = np.sin(alpha)

        # Compute the induced lift force on each lifting surface
        outputs['L'] = np.sum(-forces[:, 0] * sina + forces[:, 2] * cosa)

        # Compute the induced drag force on each lifting surface
        outputs['D'] = np.sum( forces[:, 0] * cosa + forces[:, 2] * sina)

        if self.surface['symmetry']:
            outputs['D'] *= 2
            outputs['L'] *= 2

    def compute_partial_derivs(self, inputs, outputs, partials):
        """ Jacobian for lift and drag."""

        # Analytic derivatives for sec_forces
        alpha = float(inputs['alpha']) * np.pi / 180.
        cosa = np.cos(alpha)
        sina = np.sin(alpha)

        forces = inputs['sec_forces']

        if self.surface['symmetry']:
            symmetry_factor = 2.
        else:
            symmetry_factor = 1.

        tmp = np.array([-sina, 0, cosa])
        partials['L', 'sec_forces'] = \
            np.atleast_2d(np.tile(tmp, self.num_panels)) * symmetry_factor
        tmp = np.array([cosa, 0, sina])
        partials['D', 'sec_forces'] = \
            np.atleast_2d(np.tile(tmp, self.num_panels)) * symmetry_factor

        p180 = np.pi / 180.
        partials['L', 'alpha'] = p180 * symmetry_factor * \
            np.sum(-forces[:, :, 0] * cosa - forces[:, :, 2] * sina)
        partials['D', 'alpha'] = p180 * symmetry_factor * \
            np.sum(-forces[:, :, 0] * sina + forces[:, :, 2] * cosa)