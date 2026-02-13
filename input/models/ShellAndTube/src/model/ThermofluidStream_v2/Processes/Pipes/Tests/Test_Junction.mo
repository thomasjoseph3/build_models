within ThermofluidStream_v2.Processes.Pipes.Tests;
model Test_Junction
  extends Modelica.Icons.Example;

  replaceable package Medium = ThermofluidStream_v2.Media.myMedia.Air.DryAirNasa constrainedby
    ThermofluidStream_v2.Media.myMedia.Interfaces.PartialMedium
    annotation(choicesAllMatching = true);

  inner ThermofluidStream_v2.DropOfCommons dropOfCommons(displayInstanceNames=true, displayParameters=true)
    annotation (Placement(transformation(extent={{-100,80},{-80,100}})));
  ThermofluidStream_v2.Processes.Pipes.JunctionY junctionY(
    redeclare package Medium = Medium,
    assumeConstantDensity=true,
    d_straight=0.1,
    d_branching=0.05,
    alpha=0.78539816339745) annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  ThermofluidStream_v2.Boundaries.Sink sink(redeclare package Medium = Medium, p0_par=100000) annotation (Placement(transformation(extent={{60,-10},{80,10}})));
  ThermofluidStream_v2.Boundaries.Source source(
    redeclare package Medium = Medium,
    p0_par=200000,
    T0_par=293.15) annotation (Placement(transformation(extent={{-40,-10},{-20,10}})));
  ThermofluidStream_v2.Boundaries.Source source1(
    redeclare package Medium = Medium,
    p0_par=200000,
    T0_par=293.15) annotation (Placement(transformation(extent={{-74,20},{-54,40}})));
  ThermofluidStream_v2.Processes.FlowResistance flowResistance(
    redeclare package Medium = Medium,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    m_flow_0=dropOfCommons.m_flow_reg,
    redeclare function pLoss =
        ThermofluidStream_v2.Processes.Internal.FlowResistance.laminarTurbulentPressureLoss,
    l=1,
    r=1e-2) annotation (Placement(transformation(extent={{20,-10},{40,10}})));
  FlowResistance                             flowResistance1(
    redeclare package Medium = Medium,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    m_flow_0=0,
    redeclare function pLoss = ThermofluidStream_v2.Processes.Internal.FlowResistance.laminarTurbulentPressureLoss,
    l=1,
    r=1e-2) annotation (Placement(transformation(extent={{-44,20},{-24,40}})));
equation
  connect(junctionY.outlet, flowResistance.inlet)
    annotation (Line(
      points={{10,0},{20,0}},
      color={28,108,200},
      thickness=0.5));
  connect(sink.inlet, flowResistance.outlet) annotation (Line(
      points={{60,0},{40,0}},
      color={28,108,200},
      thickness=0.5));
  connect(junctionY.inlet_straight, source.outlet)
    annotation (Line(
      points={{-10,0},{-20,0}},
      color={28,108,200},
      thickness=0.5));
  connect(source1.outlet, flowResistance1.inlet)
    annotation (Line(
      points={{-54,30},{-44,30}},
      color={28,108,200},
      thickness=0.5));
  connect(flowResistance1.outlet, junctionY.inlet_branching)
    annotation (Line(
      points={{-24,30},{-6,30},{-6,8}},
      color={28,108,200},
      thickness=0.5));
  annotation (Icon(coordinateSystem(preserveAspectRatio=false)), Diagram(
        coordinateSystem(preserveAspectRatio=false)));
end Test_Junction;
