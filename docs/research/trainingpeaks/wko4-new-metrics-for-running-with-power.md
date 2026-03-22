---
title: "WKO4: New Metrics for Running With Power"
author: "Dr. Andrew Coggan, Ph.D."
source: "https://www.trainingpeaks.com/blog/wko4-new-metrics-for-running-with-power/"
score: 24
skills: ["wko5-training"]
relevance: "power_duration, tte, training_load, muscle_science"
trusted_author: true
---

Running with power is a new frontier, and there are many questions that are still unanswered. However, Dr. Andrew Coggan continues to find new metrics that add understanding and meaning to the data. Learn about the new Run Dashboard he has created, which include four new charts and several new metrics.
The increasing availability and popularity of wearable sensors for runners and triathletes has opened up new, and potentially quite useful, avenues for data analysis. As emphasized by Dr. Steve McGregor of Eastern Michigan University, and to paraphrase SRM’s long-standing catchphrase, such devices can “make your body a mobile biomechanics laboratory.” However, in contrast to cycling power measurements, interpretation of this new running data is somewhat less straight-forward. Deep insight will likely only be achieved via further experience and experimentation.
To aid in this quest, I have created a new Running Dashboard for WKO4. This Dashboard contains a number of charts and reports that display and summarize data likely to be relevant to anyone interested in running performance. This brief article describes these measurements, what they mean, and why they might be important.
Horizontal Running Chart
This chart displays the following data, along with a map of your route as a child chart.
Power (W/kg):
Running power relative to body mass, as measured using a running power meter. Note that because of energy recycling via the series-elastic elements of the musculoskeletal system, sustained running power is often significantly higher than cycling power, even for the same individual. On the other hand, due to the way the data is smoothed or damped, power at very short durations is generally lower. This smoothing also tends to limit the accuracy, and hence the usefulness, of the WKO4 power-duration model when applied to running, even though the latter conceptually applies to all modes of exercise, not just cycling.
Pace (min/km):
Running pace
Heart Rate (beats/min):
Heart rate
Elevation (m):
Elevation
Running Effectiveness Chart
This chart displays the following data, along with averages for the range selected in the Right Hand Explorer (excluding periods where speed is <1.5 m/s, under the assumption that such points represent walking or standing, not running).
Power (W/kg):
Running power is repeated here, since it is used to calculate running effectiveness (see below).
Speed (m/s):
Running speed, i.e., inverse of pace. Presented because it is also a component of running effectiveness (see below).
Running Effectiveness (kg/N):
Running effectiveness is a novel metric presently unique to WKO4. It is calculated as the ratio of speed (in m/s) to power (in W/kg, or (Nm/s)/kg), resulting in the units of kg/N. It can be viewed as the inverse of the effective horizontal retarding force that a runner must overcome to achieve a particular speed. For most experienced runners, running effectiveness is typically close to 1 kg/N. Running effectiveness may be lower in novice or fatigued runners since they do not travel as fast for a given power output or must generate more power to achieve the same speed. Running effectiveness may also decline slightly at higher running speeds, when running above critical pace for example.
Note that running effectiveness is not the same as running economy or running efficiency. The former is the ratio of metabolic cost, i.e., VO
2
or sometimes metabolic power, which accounts for small differences in energy yield per unit of O
2
consumed, to running speed. The latter is the ratio of external mechanical power output to metabolic power production.
Elevation (m):
Elevation is also repeated here, as speed, and hence running effectiveness, will vary at the same power output, depending on whether one is running uphill, downhill, or on level ground.
Running Dynamics Chart
This chart (named for Garmin’s Running Dynamics) displays the following data channels, along with averages for the range selected in the Right Hand Explorer (excluding periods where speed is <1.5 m/s, under the assumption that such points represent walking or standing, not running):
Step Rate (steps/min):
Also termed stride rate or, outside of the scientific literature, cadence. This is the number of steps or strides taken per minute. Contrary to common lore, a step rate or stride rate of 180 (or greater) steps/min is not necessarily ideal. Rather, the optimum varies between individuals, based on their running speed, leg length, leg stiffness (Kleg – see below), etc.
Ground Contact Time (ms):
Also called stance time, this measurement reflects how long the foot is contact with the ground, starting from the initial “crash” phase as the runner touches down and ending with toe-off. Values are typically in the 150 to 350 ms range, although this varies somewhat based on running speed, etc. Ground contact time is of potential interest because studies in the literature suggest that shorter ground contact times may be associated with a lower metabolic cost to run at the same speed.
Vertical Oscillation (cm):
Vertical oscillation is how much your center-of-mass bounces or travels up-and-down while running. Values are generally in the 8 to 14 cm range, although again it varies depending on a number of factors, including running speed. Running faster generally entails “flying higher” since they are achieved in part by increasing stride length, which requires a higher apogee during the flight phase. At a given running speed, excessive vertical oscillation generally results in poor running economy as excess energy is expended performing work against gravity. On the other hand, overly constraining vertical oscillation at a given running speed may also impair running economy as this can limit energy recycling.
Elevation (m):
Elevation is also repeated here, as whether one is running uphill, downhill, or on level ground can obviously influence the other measurements in the chart.
Running Biomechanics Chart
Like the Running Effectiveness Chart, this chart displays data unique to WKO4, along with averages for the range selected in the Right Hand Explorer (excluding periods where speed is <1.5 m/s, under the assumption that such points represent walking or standing, not running):
Duty Factor (%):
As indicated above, shorter ground contact times may be associated with better running economy. However, ground contact time varies somewhat based on running speed, making it more difficult to interpret. Duty factor, on the other hand, is the percentage of the total time between steps or strides that the foot is on the ground. As such, it somewhat less dependent on actual running speed. Values for duty factor can vary from 50 to 90 percent, but are typically in the 60 to 80 percent range.
Flight Time (ms):
This is the time during which both feet are off the ground. All else being equal, a greater flight time might be associated with better running economy, since at a given step or stride frequency, flight time and ground contact time are inverse to each other.
Kleg (kN/m):
A simple, yet surprisingly accurate, model of the biomechanics of “upright bipedal locomotion” (walking or running) is a point (i.e., infinitely small/dense) mass on a spring. In other words, walking or running can be modeled fairly accurately as a series of forward bounces or hops, during which the legs acts as springs that are alternately compressed upon landing and released upon take-off.
This spring-like behavior enables significant energy recycling to occur, thus reducing the metabolic energy cost of running at any given speed or, alternatively, increasing the speed of running for a given metabolic rate. The apparent spring constant, Kleg, which is a function of both anatomical (passive) and physiological (active) factors, is therefore correlated with running economy. That is, individuals with stiffer “springs” rebound off the ground more readily, minimizing the need for their muscles to generate force and the time during which they must do so.
WKO4 therefore employs a validated mathematical model drawn from the scientific literature to calculate Kleg, thus for the first time making this measurement available outside of a laboratory setting. Kleg is typically in the 4 to 12 kN/m range. Notably, Kleg is not heavily influenced by running speed, but may change somewhat over the course of a longer run due to fatigue.
Fmax (N or g):
Fmax is the maximum impact force experienced when the runner’s foot hits the ground, measured in units of either newtons or g force. Calculated using the same model as Kapp, Fmax is of potential interest from an injury risk perspective. Values are typically 2 to 3 g, in other words, 2 to 3 times an individual’s body mass.
Elevation (m):
Elevation is also repeated here, as whether one is running uphill, downhill, or on level ground can obviously influence the other measurements in the chart.
Running with power is in its infancy and these new metrics will provide the foundation of more innovation in the world of running with power. Over the course of the next few months we will continue to work with our “running with power” beta team to bring new metrics to life, focusing on tracking and analyzing power data to better understand how to use in training and race performance.
To learn how to participate in the running with power please join the WKO4 User Group on Facebook:
https://www.facebook.com/groups/WKO4powerusers/
About Dr. Andrew Coggan, Ph.D.
Andrew R. Coggan, Ph.D., is an internationally recognized exercise physiologist. He has published numerous scientific articles on the physiological responses and adaptations to acute and chronic exercise in healthy untrained individuals, athletes, the elderly, and various patient populations. A former national-caliber masters cyclist and TT record holder, Dr. Coggan is also widely recognized as one of the leading experts on the use of power meters. He is the originator of numerous concepts/algorithms for analyzing the data that such devices provide, including normalized power, TSS, power profiling, quadrant analysis, the Performance Manager, the WKO4 power-duration model, auto-phenotyping, and unique pedaling metrics. In 2006, he was honored for these applied sports science efforts with USA Cycling’s Sport Science Award and by being named as one of three Finalists for the US Olympic Committee’s Doc Councilman Award.
#data-analysis
#performance
#running
