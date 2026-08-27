# PDF Report Generator

## Stage 4 and 5 Answers

Stage 4:

I would move the long work of generating a whole report in the endpoint itself when I expect the report to be larger than 10 MB.

Stage 5:

The check prevents duplicate expensive work when a user (or an impatient client) submits the same request repeatedly.

One real world example where not having the check costs a lot is a monthly invoice endpoint where if a user clicks on "generate" many times, storage will be wasted and computing power will be wasted on workers doing the same job over and over.