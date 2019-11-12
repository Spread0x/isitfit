## isitfit / cost / Redshift

isitfit cost module for AWS Redshift clusters


### TODO Note by Shadi on 2019-11-12:

This module isn't directly integrated in
the `isitfit.cost.utilizationListener` and `...optimizationListener` classes
because I want to improve the architecture.

I would like to add a `isitfit.cost.ec2` module, similar to `isitfit.cost.redshift`,
and then the `isitfit.cost.mainManager` should be able to handle both
and merge results into 1 table.

This requires to split the `utilizationListener` into `iterator, analyzer, reporter`
similar to the `redshift` module.
The remaining part of `utilizationListener` would be what stays back in `mainManager`
