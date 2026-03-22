// Power Duration model — Bayesian estimation with informative FTP prior
//
// P(t) = Pmax * exp(-t/tau) + FRC * 1000 / (t + t0) + mFTP
//
// Prior on mFTP comes from last coach-tested FTP (Kolie Moore protocol).
// Tightness of prior depends on how recent the test was.

data {
  int<lower=1> N;                // number of MMP durations
  array[N] real duration_s;      // durations in seconds
  array[N] real observed_power;  // best power at each duration
  real ftp_prior_mean;           // from last FTP test
  real<lower=1> ftp_prior_sd;   // tighter = more recent test
}

parameters {
  real<lower=400, upper=2000> Pmax;
  real<lower=5, upper=50> FRC;       // kJ
  real<lower=100, upper=450> mFTP;
  real<lower=3, upper=60> tau;
  real<lower=0.5, upper=20> t0;
  real<lower=5, upper=100> sigma;    // observation noise
}

model {
  // Priors
  Pmax ~ normal(1100, 300);
  FRC ~ normal(20, 8);
  mFTP ~ normal(ftp_prior_mean, ftp_prior_sd);  // KEY: informed by coach test
  tau ~ normal(15, 8);
  t0 ~ normal(5, 3);
  sigma ~ normal(20, 10);

  // Likelihood: MMP observations follow the PD curve with noise
  for (i in 1:N) {
    real t = duration_s[i];
    real predicted = Pmax * exp(-t / tau) + FRC * 1000 / (t + t0) + mFTP;
    observed_power[i] ~ normal(predicted, sigma);
  }
}

generated quantities {
  // Derived quantities
  real mVO2max_ml_min_kg = (mFTP * 60.0 * 1000.0) / (0.23 * 20900.0) / 78.0;
  real TTE_min = tau * log(Pmax / (FRC * 1000.0 / tau));  // approximate
}
