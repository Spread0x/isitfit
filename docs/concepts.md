# Concepts

Some jargon and its explanation

---


## Cost-weighted average utilization

What's that?

Say we have 2 machines A and B:

- Machine A costs  1 $/day, its CPU is used at 90%, and its memory is used at 80%.
- Machine B costs 10 $/day, its CPU is used at 10%, and its memory is used at 10% also.

The un-normalized average utilization would be

```
( 90% + 80% + 10% + 10% ) / 4
  ~ 47 %
```

The Cost-Weighted Average Utilization would be:

```
( 1 $/day * (90% + 80%)/2 + 10 $/day * (10% + 10%)/2 ) / (1$/day + 10$/day)
  =  (0.85 $/day + 1 $/day) / (11 $/day)
  ~ 16 %
```

The Cost-Weighted Average Utilization in the above example is much lower than the un-normalized average
because it gives more weight to the underused and more expensive machine B
than it does to the heavily-used and cheaper machine A.




## Underused, Overused, Idle, Normal, Burstable

isitfit categorizes instances as:

- Idle: this is an EC2 server that's sitting there doing nothing over the past 90 days
- Underused: this is an EC2 server that can be downsized at least one size
- Overused: this is an EC2 server whose usage is concentrated
- Normal: EC2 servers for whom isitfit doesn't have any recommendations


A finer degree of categorization specifies:

- Burstable: this is for EC2 servers whose workload has spikes. These can benefit from burstable machine types (aws ec2's t2 family), or moved into separate lambda functions. The server itself can be downsized at least twice afterwards.


The above categories are currently rule-based, generated from the daily cpu utilization of the last 90 days (fetched from AWS Cloudwatch).

- idle: If the maximum over 90 days of daily maximum is < 3%
- underused: If it's < 30%
- underused, convertible to burstable, if:
  - it's > 70%
  - the average daily max is also > 70%
  - but the maximum of the daily average < 30%

Sizing is simply a rule that says: "If underused, recommend the next smaller instance within the same family. If overused, recommend the next larger one."

The relevant source code is [here](https://github.com/autofitcloud/isitfit/blob/master/isitfit/optimizerListener.py#L69)



