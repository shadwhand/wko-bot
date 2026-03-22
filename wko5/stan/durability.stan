// Durability decay model — Bayesian estimation
//
// degradation = a * exp(-b * kJ / 1000) + (1-a) * exp(-c * hours)
//
// Fitted from windowed MMP ratios across long rides.

data {
  int<lower=1> N;
  array[N] real cum_kj;
  array[N] real elapsed_h;
  array[N] real ratio;       // MMP ratio: window power / first window power
}

parameters {
  real<lower=0.01, upper=0.99> a;
  real<lower=0.0001, upper=0.05> b;
  real<lower=0.001, upper=1.0> c;
  real<lower=0.01, upper=0.3> sigma;
}

model {
  a ~ beta(4, 4);
  b ~ lognormal(-5, 1.5);
  c ~ lognormal(-3, 1);
  sigma ~ exponential(10);

  for (i in 1:N) {
    real pred = a * exp(-b * cum_kj[i] / 1000) + (1 - a) * exp(-c * elapsed_h[i]);
    ratio[i] ~ normal(pred, sigma);
  }
}
