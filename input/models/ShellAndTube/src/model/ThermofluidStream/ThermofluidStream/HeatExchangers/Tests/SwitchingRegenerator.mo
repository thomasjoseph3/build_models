within ThermofluidStream.HeatExchangers.Tests;
model SwitchingRegenerator "Regenerative Heat Exchanger using Switching Beds"
  extends Modelica.Icons.Example;

  replaceable package Medium = Media.myMedia.Air.DryAirNasa
    constrainedby Media.myMedia.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  // Control Signal
  // Period 20s: 10s Hot Flow, 10s Cold Flow
  Modelica.Blocks.Sources.BooleanPulse switchSignal(period=20, width=50)
    annotation (Placement(transformation(extent={{-80,80},{-60,100}})));
    
  Modelica.Blocks.Math.BooleanToReal boolToReal(realTrue=1, realFalse=0)
    annotation (Placement(transformation(extent={{-40,80},{-20,100}})));
    
  Modelica.Blocks.Math.BooleanToReal boolToRealInv(realTrue=0, realFalse=1)
    annotation (Placement(transformation(extent={{-40,50},{-20,70}})));

  // Hot Stream (Source A -> Sink A)
  // Simulates Exhaust Gas (573 K, 300 degC)
  Boundaries.Source sourceHot(
    redeclare package Medium = Medium,
    T0_par=573.15, 
    p0_par=110000)
    annotation (Placement(transformation(extent={{-100,10},{-80,30}})));
    
  Boundaries.Sink sinkHot(
    redeclare package Medium = Medium,
    p0_par=100000)
    annotation (Placement(transformation(extent={{80,10},{100,30}})));

  // Cold Stream (Source B -> Sink B)
  // Simulates Intake Air (293 K, 20 degC)
  Boundaries.Source sourceCold(
    redeclare package Medium = Medium,
    T0_par=293.15, 
    p0_par=110000)
    annotation (Placement(transformation(extent={{80,-30},{100,-10}}, rotation=180)));
    
  Boundaries.Sink sinkCold(
    redeclare package Medium = Medium,
    p0_par=100000)
    annotation (Placement(transformation(extent={{-100,-30},{-80,-10}}, rotation=180)));

  // The Regenerative Bed (Thermal Storage)
  // Modeled as a fluid volume coupled to a large thermal mass
  Processes.ConductionElement bed(
    redeclare package Medium = Medium,
    V(displayUnit="l") = 1.0, 
    k_par=1000) // High conductance to transfer heat quickly to matrix
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
    
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor matrixMass(
    C=5000, // Thermal mass of the matrix (J/K)
    T(start=433.15)) // Initial temp (average)
    annotation (Placement(transformation(extent={{-10,-40},{10,-20}})));

  // Valves
  // Hot Path (Open when Signal = 1)
  FlowControl.TanValve v_Hot_In(
    redeclare package Medium = Medium,
    m_flow_ref=1.0,
    p_ref=5000)
    annotation (Placement(transformation(extent={{-60,10},{-40,30}})));
    
  FlowControl.TanValve v_Hot_Out(
    redeclare package Medium = Medium,
    m_flow_ref=1.0,
    p_ref=5000)
    annotation (Placement(transformation(extent={{40,10},{60,30}})));

  // Cold Path (Open when Signal = 0)
  FlowControl.TanValve v_Cold_In(
    redeclare package Medium = Medium,
    m_flow_ref=1.0,
    p_ref=5000)
    annotation (Placement(transformation(extent={{60,-30},{40,-10}}, rotation=180)));
    
  FlowControl.TanValve v_Cold_Out(
    redeclare package Medium = Medium,
    m_flow_ref=1.0,
    p_ref=5000)
    annotation (Placement(transformation(extent={{-40,-30},{-60,-10}}, rotation=180)));

  inner DropOfCommons dropOfCommons
     annotation (Placement(transformation(extent={{-100,80},{-80,100}})));

equation
  // Control Logic
  connect(switchSignal.y, boolToReal.u) annotation (Line(points={{-59,90},{-42,90}}, color={255,0,255}));
  connect(switchSignal.y, boolToRealInv.u) annotation (Line(points={{-59,90},{-50,90},{-50,60},{-42,60}}, color={255,0,255}));
  
  connect(boolToReal.y, v_Hot_In.u) annotation (Line(points={{-19,90},{-10,90},{-10,34},{-50,34},{-50,32}}, color={0,0,127}));
  connect(boolToReal.y, v_Hot_Out.u) annotation (Line(points={{-19,90},{-10,90},{-10,34},{50,34},{50,32}}, color={0,0,127}));
  
  connect(boolToRealInv.y, v_Cold_In.u) annotation (Line(points={{-19,60},{10,60},{10,-34},{50,-34},{50,-32}}, color={0,0,127}));
  connect(boolToRealInv.y, v_Cold_Out.u) annotation (Line(points={{-19,60},{10,60},{10,-34},{-50,-34},{-50,-32}}, color={0,0,127}));

  // Heat Transfer
  connect(bed.heatPort, matrixMass.port) annotation (Line(points={{0,-10},{0,-20}}, color={191,0,0}));

  // Hot Loop
  connect(sourceHot.outlet, v_Hot_In.inlet) annotation (Line(points={{-80,20},{-60,20}}, color={28,108,200}));
  connect(v_Hot_In.outlet, bed.inlet) annotation (Line(points={{-40,20},{-20,20},{-20,0},{-10,0}}, color={28,108,200}));
  connect(bed.outlet, v_Hot_Out.inlet) annotation (Line(points={{10,0},{20,0},{20,20},{40,20}}, color={28,108,200}));
  connect(v_Hot_Out.outlet, sinkHot.inlet) annotation (Line(points={{60,20},{80,20}}, color={28,108,200}));

  // Cold Loop (Counter-Flow Direction)
  connect(sourceCold.outlet, v_Cold_In.inlet) annotation (Line(points={{80,-20},{60,-20}}, color={28,108,200}));
  connect(v_Cold_In.outlet, bed.outlet) annotation (Line(points={{40,-20},{20,-20},{20,0},{10,0}}, color={28,108,200}));
  connect(bed.inlet, v_Cold_Out.inlet) annotation (Line(points={{-10,0},{-20,0},{-20,-20},{-40,-20}}, color={28,108,200}));
  connect(v_Cold_Out.outlet, sinkCold.inlet) annotation (Line(points={{-60,-20},{-80,-20}}, color={28,108,200}));

  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)), 
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-120,-100},{120,120}})),
    experiment(
      StopTime=100, // 5 cycles
      Tolerance=1e-6,
      Interval=0.1,
      __Dymola_Algorithm="Dassl"),
    Documentation(info="<html>
        <p><b>Switching Regenerator Example</b></p>
        <p>This model demonstrates a regenerative heat exchanger using a fixed bed (Thermal Mass) and periodic flow switching.</p>
        <p><b>Operation:</b></p>
        <ul>
        <li><b>Phase 1 (Heating):</b> Hot gas flows L->R, heating the matrix. Cold valves closed.</li>
        <li><b>Phase 2 (Cooling):</b> Cold gas flows R->L, absorbing heat from matrix. Hot valves closed.</li>
        <li><b>Cycle Time:</b> 20 seconds.</li>
        </ul>
        <p><b>Components:</b></p>
        <ul>
        <li><b>Bed:</b> Modeled using <code>ConductionElement</code> (Fluid) + <code>HeatCapacitor</code> (Solid).</li>
        <li><b>Valves:</b> <code>TanValve</code> used for flow switching.</li>
        </ul>
</html>"));
end SwitchingRegenerator;
