within ThermofluidStream_v2.Processes.Pipes.Tests;
model Test_EdgedOrifice
  extends Modelica.Icons.Example;

  replaceable package Medium = ThermofluidStream_v2.Media.myMedia.Air.DryAirNasa constrainedby
    ThermofluidStream_v2.Media.myMedia.Interfaces.PartialMedium
    annotation(choicesAllMatching = true);

  inner ThermofluidStream_v2.DropOfCommons dropOfCommons(displayInstanceNames=true,
      displayParameters=true)
    annotation (Placement(transformation(extent={{-100,80},{-80,100}})));

  ThermofluidStream_v2.Processes.Pipes.EdgedOrifice edgedOrifice(
    redeclare package Medium = Medium,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    d_1=1e-2,
    d_0=0.5e-2,
    l_0=0.1)  annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  ThermofluidStream_v2.Boundaries.Source source(
    redeclare package Medium = Medium,
    pressureFromInput=true,
    p0_par=200000,
    T0_par=293.15) annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  ThermofluidStream_v2.Boundaries.Sink sink(redeclare package Medium = Medium, p0_par=100000) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={40,0})));
  Modelica.Blocks.Sources.Sine sine(
    amplitude=0.4e5,
    f=3,
    offset=1.5e5,
    startTime=0.1) annotation (Placement(transformation(extent={{-80,-4},{-60,16}})));
equation
  connect(source.outlet, edgedOrifice.inlet) annotation (Line(
      points={{-30,0},{-20,0},{-10,0}},
      color={28,108,200},
      thickness=0.5,
      smooth=Smooth.Bezier));
  connect(edgedOrifice.outlet, sink.inlet) annotation (Line(
      points={{10,0},{20,0},{30,0}},
      color={28,108,200},
      thickness=0.5,
      smooth=Smooth.Bezier));
  connect(sine.y, source.p0_var) annotation (Line(points={{-59,6},{-42,6}},                   color={0,0,127}));
  annotation (Icon(coordinateSystem(preserveAspectRatio=false)), Diagram(
        coordinateSystem(preserveAspectRatio=false)));
end Test_EdgedOrifice;
