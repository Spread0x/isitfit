# Statistics and Usage Tracking

What data we collect and why

---

`isitfit` seeks to be driven by the usage and demand of the community.

We observe what users are doing by collecting various events and usage data,
and we use this data to iterate and improve `isitfit` based on this gained insight.
This includes things like the installed version of `isitfit` and the commands being used.

We do not use event payloads to collect any identifying information,
and the data is used in aggregate to understand the community as a whole.

Here is an example of a collected event:

```
Date/Time:        2019-10-05 12:34
isitfit version:  0.10
Command issued:   cost analyze
Installation ID:  abcdef123456 (random per installation)
Source IP:        123.123.123.123
Source city:      Jacksonville
Source country:   USA
```

If you use the `--share-email` option,
the email address is stored by [AWS SES](https://aws.amazon.com/ses/)
to remember that it has already been verified.
The email's contents are not stored.

(This section was adapted from [serverless](https://serverless.com/framework/docs/providers/aws/cli-reference/slstats/))



