/**
 * Panel registration index.
 * Import this file to register all panels in the PanelRegistry.
 * Each panel module calls registerPanel() as a side effect.
 *
 * Chart panels (D3) are placeholders — registered in Plan 1C.
 */

// Status
import './status/TSBStatus'
import './status/RecentRides'
import './status/ClinicalAlert'

// Health
import './health/ClinicalFlags'
import './health/IFFloor'
import './health/PanicTraining'
import './health/RedsScreen'
import './health/FreshBaseline'

// Fitness (non-chart only)
import './fitness/PowerProfile'
import './fitness/ShortPower'

// Event Prep
import './event-prep/RouteSelector'
import './event-prep/GapAnalysis'
import './event-prep/OpportunityCost'
import './event-prep/GlycogenBudget'

// History
import './history/RidesTable'
import './history/TrainingBlocks'
import './history/PhaseTimeline'
import './history/IntensityDist'

// Profile
import './profile/CogganRanking'
import './profile/Phenotype'
import './profile/PosteriorSummary'
import './profile/Feasibility'
import './profile/AthleteConfig'
