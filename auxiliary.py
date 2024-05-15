"""
@author: Bárbara Rodrigues, Daniel Kopisitskiy, Denise Cariaga Sandoval
@project: MOPTA Competition 2024 Project
"""
# Python Libraries
import pyomo.environ as pyo
import pandas as pd
import numpy as np
from dataclasses import dataclass
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition
import matplotlib.pyplot as plt

@dataclass
class InstanceMOPTA():
    ## Parameter Data
    # Sets
    Days        : set
    TimePeriods : set
    Nodes       : set
    Scenarios   : set	

    SolarNodes        : set
    WindNodes         : set
    RenewableNodes    : set
    ElectrolyzerNodes : set
    TankNodes         : set
    FuelCellNodes     : set
    LoadNodes         : set
    IndustrialNodes   : set

    Scenario_names : pd.DataFrame = pd.DataFrame()

    # Parameters
    costBuildSolar : pd.DataFrame = pd.DataFrame()
    capacitySolar  : pd.DataFrame = pd.DataFrame()
    costBuildWind  : pd.DataFrame = pd.DataFrame()
    capacityWind   : pd.DataFrame = pd.DataFrame()

    selfDischargeStorageGas  : pd.DataFrame = pd.DataFrame()
    effChargingStorageGas    : pd.DataFrame = pd.DataFrame()
    effDischargingStorageGas : pd.DataFrame = pd.DataFrame()
    capacityElectrolyzer     : pd.DataFrame = pd.DataFrame()
    maxChargeElectrolyzer    : pd.DataFrame = pd.DataFrame()
    costBuildStorageGas      : pd.DataFrame = pd.DataFrame()

    selfDischargeStorageLiquid  : pd.DataFrame = pd.DataFrame()
    effChargingStorageLiquid    : pd.DataFrame = pd.DataFrame()
    effDischargingStorageLiquid : pd.DataFrame = pd.DataFrame()
    capacityTank                : pd.DataFrame = pd.DataFrame()
    maxChargeTank               : pd.DataFrame = pd.DataFrame()
    costBuildStorageLiquid      : pd.DataFrame = pd.DataFrame()

    df_day_of_period : pd.DataFrame = pd.DataFrame()
    startPeriodOfDay : pd.DataFrame = pd.DataFrame()
    endPeriodOfDay   : pd.DataFrame = pd.DataFrame()
    scenarioWeight : pd.DataFrame = pd.DataFrame()

    capacityEdgeElectricity : pd.DataFrame = pd.DataFrame()
    capacityEdgeElectricity : pd.DataFrame = pd.DataFrame()
    capacityEdgeLiquid      : pd.DataFrame = pd.DataFrame()

    demandElectricity : pd.DataFrame = pd.DataFrame()
    demandGas         : pd.DataFrame = pd.DataFrame()

    generationSolar : pd.DataFrame = pd.DataFrame()
    generationWind  : pd.DataFrame = pd.DataFrame()	

    conversionGasLiquid      : float = 1
    conversionElectricityGas : float = 1
    efficiencyElectrolysis   : float = 1
    efficiencyLiquefaction   : float = 1
    efficiencyGasification   : float = 1
    maxLossLoadElectricity   : float = 0
    maxLossLoadGas           : float = 0
    costStorageGas           : float = 0
    costStorageLiquid        : float = 0

    ## Solution Values
    is_solution_loaded : bool = False
    optimality_status: str = 'Not Yet Solved'

    # First Stage Decisions
    buildNumSolar          : pd.DataFrame = pd.DataFrame()	
    buildNumWind           : pd.DataFrame = pd.DataFrame()	
    buildNumStorageGas     : pd.DataFrame = pd.DataFrame()	
    buildNumStorageLiquid  : pd.DataFrame = pd.DataFrame()	
    # Flow Decisions
    flowElectricity : pd.DataFrame = pd.DataFrame()	
    flowGas         : pd.DataFrame = pd.DataFrame()	
    flowLiquid      : pd.DataFrame = pd.DataFrame()	
    lossLoadElectricity : pd.DataFrame = pd.DataFrame()	
    lossLoadGas         : pd.DataFrame = pd.DataFrame()	
    # Generation Decision
    generationRenewable : pd.DataFrame = pd.DataFrame()	
    spillRenewable      : pd.DataFrame = pd.DataFrame()	
    # Storage Decisions
    storageGasSoc       : pd.DataFrame = pd.DataFrame()	
    storageGasCharge    : pd.DataFrame = pd.DataFrame()	
    storageGasDischarge : pd.DataFrame = pd.DataFrame()	
    storageLiquidSoc       : pd.DataFrame = pd.DataFrame()	
    storageLiquidCharge    : pd.DataFrame = pd.DataFrame()	
    storageLiquidDischarge : pd.DataFrame = pd.DataFrame()

    duals_E : pd.DataFrame = pd.DataFrame()
    duals_G : pd.DataFrame = pd.DataFrame()

    def __init__(self, filename:str):
        '''
        Input:
            filename - Name of the xlsx instance file
        '''
        # Read file into dictionary of dataframes for each sheet
        sheets_list = ['vertices', 'solar_params', 'wind_params', 'electrolyzer_params', 'tank_params', 'fuelcell_params',
            'electricityloads', 'industrialloads', 'time_params', 'day_params', 'scenario_params', 'electricity_edges',
            'gas_edges', 'liquid_edges', 'electricity_demand', 'gas_demand', 'solar_generation', 'wind_generation', 'scalar_params']
        dict_pd = pd.read_excel(filename, sheet_name=sheets_list)

        # Initialise Sets Data
        self.Days        = set(dict_pd['day_params']['day_id'])
        self.TimePeriods = set(dict_pd['time_params']['time_period_id'])
        self.Nodes       = set(dict_pd['vertices']['vertex_id'])
        self.Scenarios   = set(dict_pd['scenario_params']['scenario_id'])
        self.Scenario_names = dict_pd['scenario_params'][['scenario_id', 'scenario_name']]

        self.SolarNodes        = set(dict_pd['solar_params']['solar_panel_id'])
        self.WindNodes         = set(dict_pd['wind_params']['wind_turbine_id'])
        self.RenewableNodes    = self.SolarNodes.union(self.WindNodes)
        self.ElectrolyzerNodes = set(dict_pd['electrolyzer_params']['electrolyzer_id'])
        self.TankNodes         = set(dict_pd['tank_params']['liquid_tank_id'])
        self.FuelCellNodes     = set(dict_pd['fuelcell_params']['fuel_cell_id'])
        self.LoadNodes         = set(dict_pd['electricityloads']['electricity_loads_id'])
        self.IndustrialNodes   = set(dict_pd['industrialloads']['industrial_loads_id'])

        # Initialise Data in sheet 'solar_params'
        df_temp = dict_pd['solar_params'].set_index(['solar_panel_id'])
        self.costBuildSolar = df_temp['cost_building_solarpanel']
        self.capacitySolar  = df_temp['max_building_capacity']

        # Initialise Data in sheet 'wind_params'
        df_temp = dict_pd['wind_params'].set_index(['wind_turbine_id'])
        self.costBuildWind = df_temp['cost_building_turbine']
        self.capacityWind  = df_temp['max_building_capacity']

        # Initialise Data in sheet 'electrolyzer_params'
        df_temp = dict_pd['electrolyzer_params'].set_index(['electrolyzer_id'])
        self.selfDischargeStorageGas  = df_temp['self_discharge_rate_gas_tank']
        self.effChargingStorageGas    = df_temp['charge_efficiency_gas_tank']
        self.effDischargingStorageGas = df_temp['discharge_efficiency_gas_tank']
        self.capacityElectrolyzer     = df_temp['capacity_per_gas_tank']
        self.maxChargeElectrolyzer    = df_temp['max_charge_gas_tank']
        self.costBuildStorageGas      = df_temp['cost_per_gas_tank']

        # Initialise Data in sheet 'tank_params'
        df_temp = dict_pd['tank_params'].set_index(['liquid_tank_id'])
        self.selfDischargeStorageLiquid  = df_temp['self_discharge_rate_liquid_tank']
        self.effChargingStorageLiquid    = df_temp['charge_efficiency_liquid_tank']
        self.effDischargingStorageLiquid = df_temp['discharge_efficiency_liquid_tank']
        self.capacityTank                = df_temp['capacity_per_liquid_tank']
        self.maxChargeTank               = df_temp['max_charge_liquid_tank']
        self.costBuildStorageLiquid      = df_temp['cost_per_liquid_tank']

        # Initialise Data in sheet 'time_params'
        self.df_day_of_period = dict_pd['time_params'].set_index(['time_period_id'])

        # Initialise Data in sheet 'day_params'
        df_temp = dict_pd['day_params'].set_index(['day_id'])
        self.startPeriodOfDay = df_temp['start_time_period']
        self.endPeriodOfDay   = df_temp['end_time_period']

        # Initialise Data in sheet 'scenario_params'
        df_temp = dict_pd['scenario_params'].set_index(['scenario_id'])
        self.scenarioWeight = df_temp['percent_weight']

        # Initialise Data in sheet 'electricity_edges'
        df_temp = dict_pd['electricity_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeElectricity = df_temp['max_electricity_flow']

        # Initialise Data in sheet 'gas_edges'
        df_temp = dict_pd['gas_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeGas = df_temp['max_gas_flow']

        # Initialise Data in sheet 'liquid_edges'
        df_temp = dict_pd['liquid_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeLiquid = df_temp['max_liquid_flow']

        # Initialise Data in sheet 'electricity_demand'
        df_temp = dict_pd['electricity_demand'].set_index(['vertex','time_period'])
        self.demandElectricity = df_temp['demand']

        # Initialise Data in sheet 'gas_demand'
        df_temp = dict_pd['gas_demand'].set_index(['vertex','time_period'])
        self.demandGas = df_temp['demand']

        # Initialise Data in sheet 'solar_generation'
        df_temp = dict_pd['solar_generation'].set_index(['vertex','time_period','scenario'])
        self.generationSolar = df_temp['generation']

        # Initialise Data in sheet 'wind_generation'
        df_temp = dict_pd['wind_generation'].set_index(['vertex','time_period','scenario'])
        self.generationWind = df_temp['generation']	
	
        # Initialise Data in sheet 'scalar_params'
        df_temp = dict_pd['scalar_params']
        self.conversionGasLiquid      = df_temp['unit_convertion_gas_liquid'].iloc[0]
        self.conversionElectricityGas = df_temp['unit_convertion_electricity_gas'].iloc[0]
        self.efficiencyElectrolysis   = df_temp['efficiency_electrolysis'].iloc[0]
        self.efficiencyLiquefaction   = df_temp['efficiency_liquefaction'].iloc[0]
        self.efficiencyGasification   = df_temp['efficiency_gasification'].iloc[0]
        self.maxLossLoadElectricity   = df_temp['max_electricity_loss_load_percentage'].iloc[0]
        self.maxLossLoadGas           = df_temp['max_gas_loss_load_percentage'].iloc[0]
        self.costStorageGas           = df_temp['operational_cost_gas_storage'].iloc[0]
        self.costStorageLiquid        = df_temp['operational_cost_liquid_storage'].iloc[0]
        
    def load_solution(self, results:SolverResults, model:pyo.ConcreteModel):
        assert (results.solver.status != SolverStatus.unknown), f'Solutions do not exist, the model must be solved before.'
        
        # Update solution loaded and optimality status parameters
        self.is_solution_loaded = True
        if (results.solver.termination_condition == TerminationCondition.optimal):
            self.optimality_status = 'Optimal'
        elif (results.solver.termination_condition == TerminationCondition.infeasible):
            self.optimality_status = 'Infeasible'
        elif (results.solver.termination_condition == TerminationCondition.unbounded):
            self.optimality_status = 'Unbounded'
        else:
            self.optimality_status = f'Pyomo Termination Code {results.solver.status}'
        
        self.buildNumSolar = pd.DataFrame.from_dict(model.buildNumSolar.extract_values(), orient='index', columns=['buildNumSolar'])
        self.buildNumSolar.index.name = 'Solar Plant'
        self.buildNumWind = pd.DataFrame.from_dict(model.buildNumWind.extract_values(), orient='index', columns=['buildNumWind'])
        self.buildNumWind.index.name = 'Wind Plant'
        self.buildNumStorageGas = pd.DataFrame.from_dict(model.buildNumStorageGas.extract_values(), orient='index', columns=['buildNumStorageGas'])
        self.buildNumStorageGas.index.name = 'Electrolyzer'
        self.buildNumStorageLiquid = pd.DataFrame.from_dict(model.buildNumStorageLiquid.extract_values(), orient='index', columns=['buildNumStorageLiquid'])
        self.buildNumStorageLiquid.index.name = 'Hydrogen Tank'

        self.flowElectricity = pd.DataFrame.from_dict(model.flowElectricity.extract_values(), orient='index', columns=['flowElectricity'])
        self.flowElectricity.index = pd.MultiIndex.from_tuples(self.flowElectricity.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.flowGas = pd.DataFrame.from_dict(model.flowGas.extract_values(), orient='index', columns=['flowGas'])
        self.flowGas.index = pd.MultiIndex.from_tuples(self.flowGas.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.flowLiquid = pd.DataFrame.from_dict(model.flowLiquid.extract_values(), orient='index', columns=['flowLiquid'])
        self.flowLiquid.index = pd.MultiIndex.from_tuples(self.flowLiquid.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.lossLoadElectricity = pd.DataFrame.from_dict(model.lossLoadElectricity.extract_values(), orient='index', columns=['lossLoadElectricity'])
        self.lossLoadElectricity.index = pd.MultiIndex.from_tuples(self.lossLoadElectricity.index, names=('Load Area', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.lossLoadGas = pd.DataFrame.from_dict(model.lossLoadGas.extract_values(), orient='index', columns=['lossLoadGas'])
        self.lossLoadGas.index = pd.MultiIndex.from_tuples(self.lossLoadGas.index, names=('Industrial Area', 'Time Period', 'Scenario')) # Set MultiIndex 

        self.generationRenewable = pd.DataFrame.from_dict(model.generationRenewable.extract_values(), orient='index', columns=['generationRenewable'])
        self.generationRenewable.index = pd.MultiIndex.from_tuples(self.generationRenewable.index, names=('Renewable Plant', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.spillRenewable = pd.DataFrame.from_dict(model.spillRenewable.extract_values(), orient='index', columns=['spillRenewable'])
        self.spillRenewable.index = pd.MultiIndex.from_tuples(self.spillRenewable.index, names=('Renewable Plant', 'Time Period', 'Scenario')) # Set MultiIndex 
        
        self.storageGasSoc = pd.DataFrame.from_dict(model.storageGasSoc.extract_values(), orient='index', columns=['storageGasSoc'])
        self.storageGasSoc.index = pd.MultiIndex.from_tuples(self.storageGasSoc.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.storageGasCharge = pd.DataFrame.from_dict(model.storageGasCharge.extract_values(), orient='index', columns=['storageGasCharge'])
        self.storageGasCharge.index = pd.MultiIndex.from_tuples(self.storageGasCharge.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.storageGasDischarge = pd.DataFrame.from_dict(model.storageGasDischarge.extract_values(), orient='index', columns=['storageGasDischarge'])
        self.storageGasDischarge.index = pd.MultiIndex.from_tuples(self.storageGasDischarge.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.storageLiquidSoc = pd.DataFrame.from_dict(model.storageLiquidSoc.extract_values(), orient='index', columns=['storageLiquidSoc'])
        self.storageLiquidSoc.index = pd.MultiIndex.from_tuples(self.storageLiquidSoc.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.storageLiquidCharge = pd.DataFrame.from_dict(model.storageLiquidCharge.extract_values(), orient='index', columns=['storageLiquidCharge'])
        self.storageLiquidCharge.index = pd.MultiIndex.from_tuples(self.storageLiquidCharge.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.storageLiquidDischarge = pd.DataFrame.from_dict(model.storageLiquidDischarge.extract_values(), orient='index', columns=['storageLiquidDischarge'])
        self.storageLiquidDischarge.index = pd.MultiIndex.from_tuples(self.storageLiquidDischarge.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 

class ModelMOPTA(pyo.AbstractModel):    
    def __init__(self,**kwds):
        super().__init__(**kwds)
        self.__build_parameters()
        self.__build_variables()
        self.__build_constraints()
        self.__build_objective()

    def __build_parameters(self):
        # Sets-------------------------------------------------------------------------
        self.Days        = pyo.Set(within=pyo.PositiveIntegers)        
        self.TimePeriods = pyo.Set(within=pyo.PositiveIntegers)
        self.Nodes       = pyo.Set(within=pyo.PositiveIntegers)
        self.Scenarios   = pyo.Set(within=pyo.PositiveIntegers)

        self.SolarNodes        = pyo.Set(within=self.Nodes)
        self.WindNodes         = pyo.Set()
        self.RenewableNodes    = self.SolarNodes | self.WindNodes # union
        self.LoadNodes         = pyo.Set()
        self.IndustrialNodes   = pyo.Set()
        self.ElectrolyzerNodes = pyo.Set()
        self.FuelCellNodes     = pyo.Set()
        self.TankNodes         = pyo.Set()

        self.startPeriodOfDay = pyo.Param(self.Days, within=self.TimePeriods)
        self.endPeriodOfDay   = pyo.Param(self.Days, within=self.TimePeriods)
        
        # Objective parameters
        self.costBuildSolar         = pyo.Param(self.SolarNodes, within=pyo.NonNegativeReals)
        self.costBuildWind          = pyo.Param(self.WindNodes, within=pyo.NonNegativeReals)
        self.costBuildStorageGas    = pyo.Param(self.ElectrolyzerNodes, within=pyo.NonNegativeReals)
        self.costBuildStorageLiquid = pyo.Param(self.TankNodes, within=pyo.NonNegativeReals)
        self.costStorageGas         = pyo.Param(within=pyo.NonNegativeReals)
        self.costStorageLiquid      = pyo.Param(within=pyo.NonNegativeReals)
        self.scenarioWeight         = pyo.Param(self.Scenarios, within=pyo.PercentFraction)

        # Bound Parameters
        self.capacitySolar         = pyo.Param(self.SolarNodes, within=pyo.NonNegativeReals)
        self.capacityWind          = pyo.Param(self.WindNodes, within=pyo.NonNegativeReals)
        self.capacityTank          = pyo.Param(self.TankNodes, within=pyo.NonNegativeReals)
        self.capacityElectrolyzer  = pyo.Param(self.ElectrolyzerNodes, within=pyo.NonNegativeReals)
        self.maxChargeElectrolyzer = pyo.Param(self.ElectrolyzerNodes, within=pyo.NonNegativeReals)
        self.maxChargeTank         = pyo.Param(self.TankNodes, within=pyo.NonNegativeReals)
        self.capacityEdgeElectricity = pyo.Param(self.Nodes, self.Nodes, within=pyo.NonNegativeReals, default=0)
        self.capacityEdgeGas         = pyo.Param(self.Nodes, self.Nodes, within=pyo.NonNegativeReals, default=0)
        self.capacityEdgeLiquid      = pyo.Param(self.Nodes, self.Nodes, within=pyo.NonNegativeReals, default=0)

        self.maxLossLoadElectricity = pyo.Param(within=pyo.PercentFraction, mutable=True)
        self.maxLossLoadGas         = pyo.Param(within=pyo.PercentFraction, mutable=True)

        # Demand Parameters
        self.demandElectricity = pyo.Param(self.LoadNodes, self.TimePeriods, within=pyo.NonNegativeReals)
        self.demandGas         = pyo.Param(self.IndustrialNodes, self.TimePeriods, within=pyo.NonNegativeReals)

        # Generation Parameters
        self.generationSolar = pyo.Param(self.SolarNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.generationWind  = pyo.Param(self.WindNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        
        # Conversion Factor and Efficiency Parameters
        self.conversionElectricityGas = pyo.Param(within=pyo.NonNegativeReals)
        self.conversionGasLiquid      = pyo.Param(within=pyo.NonNegativeReals)
        self.efficiencyElectrolysis   = pyo.Param(within=pyo.PercentFraction)
        self.efficiencyLiquefaction   = pyo.Param(within=pyo.PercentFraction)
        self.efficiencyGasification   = pyo.Param(within=pyo.PercentFraction)
        
        # Battery Parameters
        self.selfDischargeStorageGas  = pyo.Param(self.ElectrolyzerNodes, within=pyo.PercentFraction)
        self.effChargingStorageGas    = pyo.Param(self.ElectrolyzerNodes, within=pyo.PercentFraction)
        self.effDischargingStorageGas = pyo.Param(self.ElectrolyzerNodes, within=pyo.PercentFraction)
        self.selfDischargeStorageLiquid  = pyo.Param(self.TankNodes, within=pyo.PercentFraction)
        self.effChargingStorageLiquid    = pyo.Param(self.TankNodes, within=pyo.PercentFraction)
        self.effDischargingStorageLiquid = pyo.Param(self.TankNodes, within=pyo.PercentFraction)

    def __build_variables(self):
        # First Stage Decisions
        self.buildNumSolar = pyo.Var(self.SolarNodes, within=pyo.NonNegativeIntegers)
        self.buildNumWind  = pyo.Var(self.WindNodes, within=pyo.NonNegativeIntegers)
        self.buildNumStorageGas     = pyo.Var(self.ElectrolyzerNodes, within=pyo.NonNegativeIntegers)
        self.buildNumStorageLiquid  = pyo.Var(self.TankNodes, within=pyo.NonNegativeIntegers)
        
        # Flow Decisions
        self.flowElectricity = pyo.Var(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.flowGas         = pyo.Var(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.flowLiquid      = pyo.Var(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)

        self.lossLoadElectricity = pyo.Var(self.LoadNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.lossLoadGas         = pyo.Var(self.IndustrialNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)

        # Generation Decision
        self.generationRenewable = pyo.Var(self.RenewableNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.spillRenewable      = pyo.Var(self.RenewableNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)

        # Storage Decisions
        self.storageGasSoc       = pyo.Var(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.storageGasCharge    = pyo.Var(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.storageGasDischarge = pyo.Var(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)

        self.storageLiquidSoc       = pyo.Var(self.TankNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.storageLiquidCharge    = pyo.Var(self.TankNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)
        self.storageLiquidDischarge = pyo.Var(self.TankNodes, self.TimePeriods, self.Scenarios, within=pyo.NonNegativeReals)

    def __build_constraints(self):
        # First Stage Constraints
        self.CbuildSolarBound = pyo.Constraint(self.SolarNodes, rule=cons_build_solar_bound)
        self.CbuildWindBound  = pyo.Constraint(self.WindNodes, rule=cons_build_wind_bound)

        # Flow Balance Constraints
        self.CflowBalanceLoads  = pyo.Constraint(self.LoadNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_loads)
        self.CflowBalanceGasLoads  = pyo.Constraint(self.IndustrialNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_gas_loads)

        self.CflowBalanceRenewables  = pyo.Constraint(self.RenewableNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_renewables)
        self.renewableGenerationDef  = pyo.Constraint(self.RenewableNodes, self.TimePeriods, self.Scenarios, rule=cons_renewable_generation_def)

        self.CflowBalanceElectrolyzers  = pyo.Constraint(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_electrolyzers)
        self.CflowBalanceTanks          = pyo.Constraint(self.TankNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_tanks)
        self.CflowBalanceFuelCells      = pyo.Constraint(self.FuelCellNodes, self.TimePeriods, self.Scenarios, rule=cons_flow_balance_fuelcells)
        
        # Battery Constraints
        self.CstorageLiquidUpdate = pyo.Constraint(self.TankNodes, self.TimePeriods, self.Scenarios, rule=cons_soc_update_storage_liquid)
        self.CstorageGasUpdate = pyo.Constraint(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, rule=cons_soc_update_storage_gas)

        self.CmaxStorageLiquid = pyo.Constraint(self.TankNodes, self.TimePeriods, self.Scenarios, rule=cons_max_capacity_storage_liquid)
        self.CmaxStorageGas    = pyo.Constraint(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, rule=cons_max_capacity_storage_gas)

        self.CmaxChargeLiquid    = pyo.Constraint(self.TankNodes, self.TimePeriods, self.Scenarios, rule=cons_max_liquid_charge_bound)
        self.CmaxDischargeLiquid = pyo.Constraint(self.TankNodes, self.TimePeriods, self.Scenarios, rule=cons_max_liquid_discharge_bound)
        self.CmaxChargeGas       = pyo.Constraint(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, rule=cons_max_gas_charge_bound)
        self.CmaxDischargeGas    = pyo.Constraint(self.ElectrolyzerNodes, self.TimePeriods, self.Scenarios, rule=cons_max_gas_discharge_bound)

        # Loss of Load Contraints
        self.CmaxLossLoadElectricity = pyo.Constraint(self.Scenarios, rule=cons_max_loss_load_electricity)
        self.CmaxLossLoadGas         = pyo.Constraint(self.Scenarios, rule=cons_max_loss_load_gas)

        # Bound Contraints
        self.CmaxFlowElectricity = pyo.Constraint(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, rule=cons_max_flow_electricity)
        self.CmaxFlowGas         = pyo.Constraint(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, rule=cons_max_flow_gas)
        self.CmaxFlowLiquid      = pyo.Constraint(self.Nodes, self.Nodes, self.TimePeriods, self.Scenarios, rule=cons_max_flow_liquid)

    def __build_objective(self):
        self.Objective_Cost = pyo.Objective(rule=obj_cost, sense=pyo.minimize)

    def build_inst(self, inst:InstanceMOPTA):
        # Create a dictionary of data in pyomo's format    
        dict_data = dict({})
        
        ## Sets & Indexes
        dict_data['Days']        = {None: list(inst.Days)}
        dict_data['TimePeriods'] = {None: list(inst.TimePeriods)}
        dict_data['Nodes']       = {None: list(inst.Nodes)}
        dict_data['Scenarios']   = {None: list(inst.Scenarios)}

        dict_data['SolarNodes']        = {None: list(inst.SolarNodes)}
        dict_data['WindNodes']         = {None: list(inst.WindNodes)}
        dict_data['LoadNodes']         = {None: list(inst.LoadNodes)}
        dict_data['IndustrialNodes']   = {None: list(inst.IndustrialNodes)}
        dict_data['ElectrolyzerNodes'] = {None: list(inst.ElectrolyzerNodes)}
        dict_data['FuelCellNodes']     = {None: list(inst.FuelCellNodes)}
        dict_data['TankNodes']         = {None: list(inst.TankNodes)}

        dict_data['startPeriodOfDay'] = inst.startPeriodOfDay.to_dict()
        dict_data['endPeriodOfDay']   = inst.endPeriodOfDay.to_dict()
        
        ## Objective parameters
        dict_data['costBuildSolar']         = inst.costBuildSolar.to_dict()
        dict_data['costBuildWind']          = inst.costBuildWind.to_dict()
        dict_data['costBuildStorageGas']    = inst.costBuildStorageGas.to_dict()
        dict_data['costBuildStorageLiquid'] = inst.costBuildStorageLiquid.to_dict()
        dict_data['costStorageGas']         = {None: inst.costStorageGas}
        dict_data['costStorageLiquid']      = {None: inst.costStorageLiquid}
        dict_data['scenarioWeight']         = inst.scenarioWeight.to_dict()

        ## Bound Parameters
        dict_data['capacitySolar']  = inst.capacitySolar.to_dict()
        dict_data['capacityWind']   = inst.capacityWind.to_dict()
        dict_data['capacityTank']          = inst.capacityTank.to_dict()
        dict_data['capacityElectrolyzer']  = inst.capacityElectrolyzer.to_dict()
        dict_data['maxChargeElectrolyzer'] = inst.maxChargeElectrolyzer.to_dict()
        dict_data['maxChargeTank']         = inst.maxChargeTank.to_dict()
        dict_data['capacityEdgeElectricity'] = inst.capacityEdgeElectricity.to_dict()
        dict_data['capacityEdgeGas']         = inst.capacityEdgeGas.to_dict()
        dict_data['capacityEdgeLiquid']      = inst.capacityEdgeLiquid.to_dict()

        dict_data['maxLossLoadElectricity'] = {None: inst.maxLossLoadElectricity}
        dict_data['maxLossLoadGas']         = {None: inst.maxLossLoadGas}

        ## Demand Parameters
        dict_data['demandElectricity'] = inst.demandElectricity.to_dict()
        dict_data['demandGas']         = inst.demandGas.to_dict()
        
        ## Generation Parameters
        dict_data['generationSolar'] = inst.generationSolar.to_dict()
        dict_data['generationWind']  = inst.generationWind.to_dict()
        
        ## Conversion Factor and Efficiency Parameters
        dict_data['conversionElectricityGas'] = {None: inst.conversionElectricityGas}
        dict_data['conversionGasLiquid']      = {None: inst.conversionGasLiquid}
        dict_data['efficiencyElectrolysis']   = {None: inst.efficiencyElectrolysis}
        dict_data['efficiencyLiquefaction']   = {None: inst.efficiencyLiquefaction}
        dict_data['efficiencyGasification']   = {None: inst.efficiencyGasification}

        ## Battery Parameters
        dict_data['selfDischargeStorageGas']  = inst.selfDischargeStorageGas.to_dict()
        dict_data['effChargingStorageGas']    = inst.effChargingStorageGas.to_dict()
        dict_data['effDischargingStorageGas'] = inst.effDischargingStorageGas.to_dict()

        dict_data['selfDischargeStorageLiquid']  = inst.selfDischargeStorageLiquid.to_dict()
        dict_data['effChargingStorageLiquid']    = inst.effChargingStorageLiquid.to_dict()
        dict_data['effDischargingStorageLiquid'] = inst.effDischargingStorageLiquid.to_dict()

        # Create Data Instance
        data = {None: dict_data}
        instance = self.create_instance(data)
        
        return instance

#------------------------------------------------------------------------------
# Auxiliary Functions to Define Constraints
#------------------------------------------------------------------------------

def cons_build_solar_bound(m:ModelMOPTA, i:int):
    return m.buildNumSolar[i] <= m.capacitySolar[i]

def cons_build_wind_bound(m:ModelMOPTA, i:int):
    return m.buildNumWind[i] <= m.capacityWind[i]

def cons_flow_balance_loads(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowElectricity[j,i,t,s] for j in m.Nodes) + m.lossLoadElectricity[i,t,s] 
    outflow = sum(m.flowElectricity[i,j,t,s] for j in m.Nodes) + m.demandElectricity[i,t]
    return inflow == outflow

def cons_flow_balance_renewables(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowElectricity[j,i,t,s] for j in m.Nodes) + m.generationRenewable[i,t,s] 
    outflow = sum(m.flowElectricity[i,j,t,s] for j in m.Nodes) + m.spillRenewable[i,t,s]
    return inflow == outflow

def cons_renewable_generation_def(m:ModelMOPTA, i:int, t:int, s:int):
    if i in m.SolarNodes:
        rhs = m.generationSolar[i,t,s] * m.buildNumSolar[i]
    elif i in m.WindNodes:
        rhs = m.generationWind[i,t,s] * m.buildNumWind[i]
    else:
        rhs = 0
    return m.generationRenewable[i,t,s] == rhs

def cons_flow_balance_gas_loads(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowGas[j,i,t,s] for j in m.Nodes) + m.lossLoadGas[i,t,s] 
    outflow = sum(m.flowGas[i,j,t,s] for j in m.Nodes) + m.demandGas[i,t]
    return inflow == outflow

def cons_flow_balance_electrolyzers(m:ModelMOPTA, i:int, t:int, s:int):
    electflow = sum(m.flowElectricity[j,i,t,s] for j in m.Nodes)
    gasflow = m.conversionElectricityGas * m.efficiencyElectrolysis * (sum(m.flowGas[i,j,t,s] for j in m.Nodes) + m.storageGasCharge[i,t,s] - m.storageGasDischarge[i,t,s])
    return electflow == gasflow

def cons_flow_balance_tanks(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowGas[j,i,t,s] for j in m.Nodes)
    outflow = m.conversionGasLiquid * m.efficiencyLiquefaction * (sum(m.flowLiquid[i,j,t,s] for j in m.Nodes) + m.storageLiquidCharge[i,t,s] - m.storageLiquidDischarge[i,t,s])
    return inflow == outflow

def cons_flow_balance_fuelcells(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = m.efficiencyGasification * (sum(m.flowGas[j,i,t,s] for j in m.Nodes) + m.conversionGasLiquid * sum(m.flowLiquid[j,i,t,s] for j in m.Nodes))
    outflow = sum(m.flowGas[i,j,t,s] for j in m.Nodes) + sum(m.flowElectricity[i,j,t,s] for j in m.Nodes)/m.conversionElectricityGas
    return inflow == outflow

def cons_soc_update_storage_liquid(m:ModelMOPTA, i:int, t:int, s:int):
    if t == min(m.TimePeriods):
        t_final = max(m.TimePeriods)
        charged = m.effChargingStorageLiquid[i] * m.storageLiquidCharge[i,t_final,s]
        discharged = 1/m.effDischargingStorageLiquid[i] * m.storageLiquidDischarge[i,t_final,s]
        return m.storageLiquidSoc[i,t,s] == (1 - m.selfDischargeStorageLiquid[i]) * m.storageLiquidSoc[i,t_final,s] + charged - discharged
    else:
        charged = m.effChargingStorageLiquid[i] * m.storageLiquidCharge[i,t-1,s]
        discharged = 1/m.effDischargingStorageLiquid[i] * m.storageLiquidDischarge[i,t-1,s]
        return m.storageLiquidSoc[i,t,s] == (1 - m.selfDischargeStorageLiquid[i]) * m.storageLiquidSoc[i,t-1,s] + charged - discharged

def cons_soc_update_storage_gas(m:ModelMOPTA, i:int, t:int, s:int):
    for d in m.Days:
        if t == m.startPeriodOfDay[d]:
            t_final = m.endPeriodOfDay[d]
            charged = m.effChargingStorageGas[i] * m.storageGasCharge[i,t_final,s]
            discharged = 1/m.effDischargingStorageGas[i] * m.storageGasDischarge[i,t_final,s]
            return m.storageGasSoc[i,t,s] == (1 - m.selfDischargeStorageGas[i]) * m.storageGasSoc[i,t_final,s] + charged - discharged
    
    charged = m.effChargingStorageGas[i] * m.storageGasCharge[i,t-1,s]
    discharged = 1/m.effDischargingStorageGas[i] * m.storageGasDischarge[i,t-1,s]
    return m.storageGasSoc[i,t,s] == (1 - m.selfDischargeStorageGas[i]) * m.storageGasSoc[i,t-1,s] + charged - discharged

def cons_max_capacity_storage_liquid(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidSoc[i,t,s] <= m.capacityTank[i] * m.buildNumStorageLiquid[i]

def cons_max_capacity_storage_gas(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasSoc[i,t,s] <= m.capacityElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_gas_charge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasCharge[i,t,s] <= m.maxChargeElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_gas_discharge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasDischarge[i,t,s] <= m.maxChargeElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_liquid_charge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidCharge[i,t,s] <= m.maxChargeTank[i] * m.buildNumStorageLiquid[i]

def cons_max_liquid_discharge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidDischarge[i,t,s] <= m.maxChargeTank[i] * m.buildNumStorageLiquid[i]

def cons_max_loss_load_electricity(m:ModelMOPTA, s:int):
    rhs = m.maxLossLoadElectricity * sum(m.demandElectricity[i,t] for i in m.LoadNodes for t in m.TimePeriods)
    return sum(m.lossLoadElectricity[i,t,s] for i in m.LoadNodes for t in m.TimePeriods) <= rhs

def cons_max_loss_load_gas(m:ModelMOPTA, s:int):
    rhs = m.maxLossLoadGas * sum(m.demandGas[i,t] for i in m.IndustrialNodes for t in m.TimePeriods)
    return sum(m.lossLoadGas[i,t,s] for i in m.IndustrialNodes for t in m.TimePeriods) <= rhs

def cons_max_flow_electricity(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    return m.flowElectricity[i,j,t,s] <= m.capacityEdgeElectricity[i,j]

def cons_max_flow_gas(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    return m.flowGas[i,j,t,s] <= m.capacityEdgeGas[i,j]

def cons_max_flow_liquid(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    return m.flowLiquid[i,j,t,s] <= m.capacityEdgeLiquid[i,j]

def obj_cost(m:ModelMOPTA):
    # Investement Costs
    cost_build_solar = sum(m.costBuildSolar[i]*m.buildNumSolar[i] for i in m.SolarNodes)
    cost_build_wind  = sum(m.costBuildWind[i]*m.buildNumWind[i] for i in m.WindNodes)

    cost_build_storage_gas = sum(m.costBuildStorageGas[i]*m.buildNumStorageGas[i] for i in m.ElectrolyzerNodes)
    cost_build_storage_liquid = sum(m.costBuildStorageLiquid[i]*m.buildNumStorageLiquid[i] for i in m.TankNodes)

    # Operational Costs
    cost_storage_gas = sum(m.scenarioWeight[s] * (sum(m.costStorageGas*m.storageGasSoc[i,t,s] for i in m.ElectrolyzerNodes for t in m.TimePeriods)) for s in m.Scenarios)
    cost_storage_liquid = sum(m.scenarioWeight[s] * (sum(m.costStorageLiquid*m.storageLiquidSoc[i,t,s] for i in m.TankNodes for t in m.TimePeriods)) for s in m.Scenarios)
    
    return cost_build_solar + cost_build_wind + cost_build_storage_gas + cost_build_storage_liquid + cost_storage_gas + cost_storage_liquid

#------------------------------------------------------------------------------
# Auxiliary Functions to Deal with Solutions
#------------------------------------------------------------------------------

def fix_integer_variables(model:pyo.ConcreteModel):
    '''
    NOTE: Model object must have a solution loaded
    '''
    # Get solution values of integer variables
    buildNumSolar_val = model.buildNumSolar.extract_values()
    buildNumWind_val  = model.buildNumWind.extract_values()
    buildNumStorageGas_val    = model.buildNumStorageGas.extract_values()
    buildNumStorageLiquid_val = model.buildNumStorageLiquid.extract_values()

    # Relax integrality on variables
    model.buildNumSolar.domain = pyo.NonNegativeReals
    model.buildNumWind.domain  = pyo.NonNegativeReals
    model.buildNumStorageGas.domain    = pyo.NonNegativeReals
    model.buildNumStorageLiquid.domain = pyo.NonNegativeReals

    # Fix variable value
    for i in model.SolarNodes:
        model.buildNumSolar[i].fix(buildNumSolar_val[i])
    for i in model.WindNodes:
        model.buildNumWind[i].fix(buildNumWind_val[i])
    for i in model.ElectrolyzerNodes:
        model.buildNumStorageGas[i].fix(buildNumStorageGas_val[i])
    for i in model.TankNodes:
        model.buildNumStorageLiquid[i].fix(buildNumStorageLiquid_val[i])

    return model

def run_solve(model:pyo.ConcreteModel, solver_name:str="gurobi_direct", warmstart:bool=False):
    opt = pyo.SolverFactory(solver_name) # Select solver
    results = opt.solve(model, load_solutions=False, warmstart=warmstart) # Solve model

    return results

def run_optimality_check(results, model:pyo.ConcreteModel):
    if results.solver.termination_condition == TerminationCondition.optimal:
        print("Model is optimal")
        model.solutions.load_from(results)
    else:
        print(f"Termination Status: {results.solver.termination_condition} \n Termination message: {results.solver.termination_message} \n Results {results}")
    
    return model

def store_solution(instance:pyo.ConcreteModel, filename:str):
    '''
    Documentation: Store variables in `instance` to a file named `file_name`
    '''
    # Open the Pandas Excel writer
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    # Iterate over variables in the model
    for var in instance.component_objects(pyo.Var, active=True): 
        # Store solutions to a dataframe 
        df = pd.DataFrame.from_dict(var.extract_values(), orient='index', columns=[str(var)])
        # Upload solutions to excel sheet with correspoding name
        df.to_excel(writer, sheet_name=str(var), index=True)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

def run_economical_analysis(model:pyo.ConcreteModel, ll_perc_lb:float, ll_perc_ub:float, ll_perc_step:float):
    assert ((ll_perc_lb>=0) & (ll_perc_lb <=1)), f"The parameter 'll_perc_lb'={ll_perc_lb} must be a percentage."
    assert ((ll_perc_ub>=0) & (ll_perc_ub <=1)), f"The parameter 'll_perc_ub'={ll_perc_ub} must be a percentage."
    assert ((ll_perc_step>=0) & (ll_perc_step <=1)), f"The parameter 'll_perc_step'={ll_perc_step} must be between 0 and 1."

    ll_perc_E = ll_perc_lb
    ll_perc_G = ll_perc_lb
    df_results = pd.DataFrame(columns=['ll_perc_E', 'll_perc_G', 'investment_solar','investment_wind',
                                       'investment_storage_gas','investment_storage_liquid',
                                       'investment_cost', 'operational_cost']
                              + [f"operational_cost_{s}" for s in model.Scenarios] 
                              + [f"ll_dual_E_{s}" for s in model.Scenarios]
                              + [f"ll_dual_G_{s}" for s in model.Scenarios])
    
    for ll_perc_E in np.arange(ll_perc_lb, ll_perc_ub+ll_perc_step, ll_perc_step):
        for ll_perc_G in np.arange(ll_perc_lb, ll_perc_ub+ll_perc_step, ll_perc_step):
            print(f"Elect = {ll_perc_E} | Gas = {ll_perc_G}")
            # Update Maximum Loss Load Parameter
            model.maxLossLoadElectricity = ll_perc_E
            model.maxLossLoadGas = ll_perc_G

            # Run MILP Model
            results = run_solve(model, warmstart=True)
            model = run_optimality_check(results, model)

            # Get optimal OPERATIONAL Costs
            cost_build_solar = sum(model.costBuildSolar[i]*pyo.value(model.buildNumSolar[i]) for i in model.SolarNodes)
            cost_build_wind  = sum(model.costBuildWind[i]*pyo.value(model.buildNumWind[i]) for i in model.WindNodes)
            cost_build_storage_gas = sum(model.costBuildStorageGas[i]*pyo.value(model.buildNumStorageGas[i]) for i in model.ElectrolyzerNodes)
            cost_build_storage_liquid = sum(model.costBuildStorageLiquid[i]*pyo.value(model.buildNumStorageLiquid[i]) for i in model.TankNodes)
            investment_cost = cost_build_solar + cost_build_wind + cost_build_storage_gas + cost_build_storage_liquid

            # Fix investement decision, relax integrality and re-solve LP
            LPmodel = fix_integer_variables(model)
        
            # Re-run model
            if (ll_perc_E == ll_perc_lb) and (ll_perc_G == ll_perc_lb):
                LPmodel.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) #Needed to export dual values later
            results2 = run_solve(LPmodel, warmstart=True)
            LPmodel = run_optimality_check(results2, LPmodel)
            
            # Get optimal OPERATIONAL Costs
            cost_storage_gas = {s: (sum(LPmodel.costStorageGas * pyo.value(LPmodel.storageGasSoc[i,t,s])\
                                        for i in LPmodel.ElectrolyzerNodes for t in LPmodel.TimePeriods)) for s in LPmodel.Scenarios}
            cost_storage_liquid = {s: (sum(LPmodel.costStorageLiquid * pyo.value(LPmodel.storageLiquidSoc[i,t,s])\
                                        for i in LPmodel.TankNodes for t in LPmodel.TimePeriods)) for s in LPmodel.Scenarios}
            operarional_costs = {s: cost_storage_gas[s] + cost_storage_liquid[s] for s in LPmodel.Scenarios}

            # Compute Loss of Load Duals/Prices
            duals_E = {s: LPmodel.dual[LPmodel.CmaxLossLoadElectricity[s]] for s in LPmodel.Scenarios}
            duals_G = {s: LPmodel.dual[LPmodel.CmaxLossLoadGas[s]] for s in LPmodel.Scenarios}

            # Update dataframe of results
            new_row = {'ll_perc_E': ll_perc_E, 
                       'll_perc_G': ll_perc_G,
                       'investment_solar': cost_build_solar,
                       'investment_wind': cost_build_wind,
                       'investment_storage_gas': cost_build_storage_gas,
                       'investment_storage_liquid': cost_build_storage_liquid,
                       'investment_cost': investment_cost,
                       'operational_cost': sum(operarional_costs[s] for s in LPmodel.Scenarios)}
            for s in LPmodel.Scenarios:
                new_row[f"operational_cost_{s}"] = operarional_costs[s]
                new_row[f"ll_dual_E_{s}"] = duals_E[s]
                new_row[f"ll_dual_G_{s}"] = duals_G[s]

            df_results = pd.concat([df_results, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    return df_results

def plot_economical_analysis(data_filename:str, scenario:int, scenario_name:str, z_axis:str, fig_filename:str, num_tol:int=0.00001):
    assert z_axis in ['operational_cost', 'dual_E', 'dual_G'], f"z_axis argument must be one of ['operational_cost', 'dual_E', 'dual_G']"
    
    # Read data and save column names
    df = pd.read_csv(data_filename)
    x_name = 'll_perc_E'
    y_name = 'll_perc_G'
    df[x_name] = df[x_name] * 100
    df[y_name] = df[y_name] * 100

    if z_axis == 'operational_cost':
        z_name  = f'operational_cost_'+str(scenario)
        z_cmap  = 'RdYlGn_r'
        z_title = f'Operational Cost \n of Scenario {scenario_name}'
    elif z_axis == 'dual_E':
        z_name  = f'll_dual_E_'+str(scenario)
        z_cmap  = 'RdYlGn'
        z_title = f'Shadow Price of Lost Electricity Load \n under Scenario {scenario_name}'
    else: # z_axis == 'dual_G'
        z_name  = f'll_dual_G_'+str(scenario)
        z_cmap  = 'RdYlGn'
        z_title = f'Shadow Price of Lost Gas Load \n under Scenario {scenario_name}'

    # 2D-arrays from DataFrame
    x1 = np.linspace(df[x_name].min(), df[x_name].max(), len(df[x_name].unique()))
    y1 = np.linspace(df[y_name].min(), df[y_name].max(), len(df[y_name].unique()))
    x, y = np.meshgrid(x1, y1)

    n_row, n_col = x.shape
    z = np.absolute(np.array([[float(df.loc[(np.abs(df[x_name]-x[i,j])<num_tol) & (np.abs(df[y_name]-y[i,j])<num_tol), z_name])
                               for j in range(n_col)] for i in range(n_row)]))    
    # Set up axes and put data on the surface
    fig = plt.figure()
    axes = fig.add_subplot(projection='3d')
    axes.plot_surface(x, y, z, cmap=z_cmap)

    # Customize labels
    axes.set_xlabel('Electricity Loss of Load (%)')
    axes.set_ylabel('Gas Loss of Load (%)')
    axes.set_title(z_title)     

    plt.savefig(fig_filename, bbox_inches='tight', pad_inches=0.3)
    plt.close()

### END