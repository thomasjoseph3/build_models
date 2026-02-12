within ThermofluidStream.HeatExchangers;
model RegenerativeHEX "Regenerative heat exchanger (rotary heat wheel) using the epsilon-NTU method"

  extends ThermofluidStream.HeatExchangers.Internal.PartialNTU;

  parameter Boolean useFiniteMatrixCapacity = false 
    "= true to apply correction for finite matrix thermal capacity"
    annotation(Dialog(group="Matrix Properties"));
  parameter Real C_r_star(unit="1", min=1) = 5 
    "Matrix capacity ratio: (m*cp)_matrix * omega / C_min (dimensionless, >1 is typical)"
    annotation(Dialog(group="Matrix Properties", enable=useFiniteMatrixCapacity));

protected
  Real epsilon_cf "Counter-flow effectiveness (infinite matrix capacity)";
  Real Phi "Correction factor for finite matrix capacity";

equation
  // Counter-flow effectiveness (valid for infinite matrix capacity / large C_r_star)
  // This is the limiting case where the regenerator behaves like a perfect counter-flow HEX
  epsilon_cf = if noEvent(C_r < 0.999) then 
    (1 - exp(-NTU*(1 - C_r))) / (1 - C_r*exp(-NTU*(1 - C_r))) 
  else 
    NTU / (1 + NTU);

  // Correction factor for finite matrix capacity (simplified Lambertson correlation)
  // Phi approaches 1 as C_r_star increases (large matrix thermal capacity)
  Phi = if useFiniteMatrixCapacity then 
    1 - exp(-C_r_star) * (1 - epsilon_cf) 
  else 
    1.0;

  // Final effectiveness
  effectiveness = epsilon_cf * Phi;

  annotation (
    Icon(coordinateSystem(preserveAspectRatio=true), graphics={
        Text(visible=displayInstanceName,
          extent={{-150,140},{150,100}},
          textString="%name",
          textColor=dropOfCommons.instanceNameColor),
        Text(visible=d1A,
          extent={{-150,-90},{150,-120}},
          textColor={0,0,0},
          textString="A = %A"),
        Text(visible=d1kNTU,
          extent={{-150,-90},{150,-120}},
          textColor={0,0,0},
          textString="k_NTU = %k_NTU"),
        Text(visible=d2kNTU,
          extent={{-150,-130},{150,-160}},
          textColor={0,0,0},
          textString="k_NTU = %k_NTU"),
        Rectangle(
          extent={{-70,66},{84,-86}},
          lineColor={215,215,215},
          fillColor={215,215,215},
          fillPattern=FillPattern.Solid,
          radius=6),
        Rectangle(
          extent={{-76,78},{76,-78}},
          lineColor={28,108,200},
          fillColor={255,255,255},
          fillPattern=FillPattern.Solid,
          radius=6),
        Ellipse(
          extent={{-50,50},{50,-50}},
          lineColor={28,108,200},
          fillColor={245,245,245},
          fillPattern=FillPattern.Solid),
        Ellipse(
          extent={{-30,30},{30,-30}},
          lineColor={28,108,200},
          fillColor={215,215,215},
          fillPattern=FillPattern.Solid),
        Line(
          points={{-50,0},{-76,0}},
          color=DynamicSelect({215,215,215}, if T_in_MediumA > T_in_MediumB then {238,46,47} else {21,85,157}),
          thickness=0.5),
        Line(
          points={{50,0},{76,0}},
          color=DynamicSelect({215,215,215}, if T_in_MediumA > T_in_MediumB then {238,46,47} else {21,85,157}),
          thickness=0.5),
        Line(
          points={{0,50},{0,78}},
          color=DynamicSelect({215,215,215}, if T_in_MediumA < T_in_MediumB then {238,46,47} else {21,85,157}),
          thickness=0.5),
        Line(
          points={{0,-50},{0,-78}},
          color=DynamicSelect({215,215,215}, if T_in_MediumA < T_in_MediumB then {238,46,47} else {21,85,157}),
          thickness=0.5),
        Polygon(
          points={{-10,0},{0,10},{10,0},{0,-10},{-10,0}},
          lineColor={28,108,200},
          fillColor={28,108,200},
          fillPattern=FillPattern.Solid),
        Text(
          extent={{-120,0},{-80,-40}},
          textColor={175,175,175},
          textString="A"),
        Text(
          extent={{80,40},{120,0}},
          textColor={175,175,175},
          textString="B"),
        Line(
          points={{-35,35},{35,-35}},
          color={28,108,200},
          thickness=0.5),
        Line(
          points={{35,35},{-35,-35}},
          color={28,108,200},
          thickness=0.5),
        Text(
          extent={{-40,74},{40,54}},
          textColor={28,108,200},
          textString="REGEN")}),
    Diagram(coordinateSystem(preserveAspectRatio=true)),
    Documentation(info="<html>
<p>Model of a <b>regenerative heat exchanger</b> (rotary heat wheel / thermal wheel) based on the effectiveness-NTU method.</p>

<h4>Description</h4>
<p>A regenerative heat exchanger transfers heat between two fluid streams through an intermediate thermal storage matrix. 
In a rotary regenerator (heat wheel), a porous matrix rotates between the hot and cold streams, 
absorbing heat from one stream and releasing it to the other.</p>

<h4>Equations</h4>
<p>For a regenerator with <b>large matrix thermal capacity</b> (C_r* >> 1), 
the effectiveness approaches that of a counter-flow heat exchanger:</p>
<pre>
  epsilon = (1 - exp(-NTU*(1-C_r))) / (1 - C_r*exp(-NTU*(1-C_r)))   for C_r < 1
  epsilon = NTU / (1 + NTU)                                         for C_r = 1
</pre>

<p>For <b>finite matrix capacity</b>, a correction factor Phi is applied:</p>
<pre>
  epsilon_actual = epsilon_counterflow * Phi
</pre>

<h4>Applications</h4>
<ul>
<li>HVAC heat recovery wheels (energy recovery ventilators)</li>
<li>Gas turbine recuperators</li>
<li>Industrial waste heat recovery</li>
<li>Cryogenic systems (Stirling engines)</li>
</ul>

<h4>References</h4>
<p>VDI Waermeatlas, Kays & London - Compact Heat Exchangers</p>
</html>"));
end RegenerativeHEX;
