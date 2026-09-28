# Client

`FireflyClient` owns an async HTTP client. Pass the Firefly III instance root
and a personal access token, then close it in a `finally` block. Read methods
return simplified domain models. Updates affect real data and may trigger
Firefly III rules and webhooks.

For an executable flow, start with [Getting started](../getting-started.md).
For skipped multipart groups and matching behavior, see
[Transactions and matching](../transactions.md).

::: ff_iii_luciferin.api.FireflyClient

::: ff_iii_luciferin.api.TransactionUpdate

::: ff_iii_luciferin.api.FireflyAPIError
