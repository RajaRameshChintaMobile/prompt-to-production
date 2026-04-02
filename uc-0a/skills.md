# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single textual complaint into its proper category and priority based on explicitly defined taxonomy rules.
    input: A dictionary containing 'complaint_id' and 'description' keys.
    output: A dictionary containing 'complaint_id', 'category', 'priority', 'reason', and 'flag' keys.
    error_handling: Return category 'Other', priority 'Low', reason 'No description provided — cannot classify.', and flag 'NEEDS_REVIEW' when the description is empty.

  - name: batch_classify
    description: Processes a batch of complaints from an input CSV file and writes classification results to an output CSV file.
    input: String path to the input CSV file and string path to the output CSV file.
    output: Writes parsed results into the output CSV file. No explicit return value.
    error_handling: Wraps individual row processing in a try/except block; on exception, writes an 'Other' row with the error cited in the reason and flag 'NEEDS_REVIEW'.
