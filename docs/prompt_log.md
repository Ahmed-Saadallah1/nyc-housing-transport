# Prompt Log

The project requires documenting every prompt used in any step. This log records the prompts given to the
AI assistant (Claude) and what each was used for. It is summarized in Section 11 of the notebook.

| # | Step | Prompt (verbatim or summarized) | Used for |
|---|------|--------------------------------|----------|
| 1 | Planning | "I wanna start doing this project. First lets decide the plan and after agreeing on it lets start execution step by step and don't move on to the next step until I confirm the previous. The most important thing is the accuracy..." (with the project description and data catalog PDFs attached) | Reading the requirements and drafting the project plan |
| 2 | Planning | "what is the main idea of the project ?" | Summary of the project's goal |
| 3 | Dataset selection | "what are the available options on datasets and why did you pick those" | Comparison of all catalog datasets; justification for H2 + T4 |
| 4 | Dataset selection | "can you get all marks from these ?" | Checking the chosen pair against every grading criterion |
| 5 | Step 1 — Setup | "confirm the dataset and keep the dash+render for now..." | Creating the repository structure and notebook header/setup section |
| 6 | Step 1 — Review | "what did that mean till now ?" (with screenshots of the Colab run) | Explanation of the setup section; fix for header line breaks |
| 7 | Step 2 — Loading | "next" | Section 2: API download helpers, collisions filter justification, caching, snapshot record |
| 8 | Step 2 — Loading | "I wanna type the cells myself" / "I wanna continue one by one ... tell me whether it contains code or text ... and explain every cell" | Cell-by-cell delivery and explanation of Section 2 |
| 9 | Step 2 — Overview | (attached housing_raw.parquet and collisions_raw.parquet) | Profiling the real snapshot to write Sections 2.3–2.5 (overview, selection reasoning, aggregation plan) |
| 10 | Step 3 — EDA | "go to it and make your explanation more summarized" | Section 3: EDA of both datasets (statistics, time/space/category charts, missingness, first cross-domain look) |
| 11 | Step 3 — EDA | "done and can we make a little compact cells ?" (chose: fewer, merged cells) | Step 3 merged into 18 cells |
| 12 | Step 3 — Fix | "where is cell 11 and 12 ?" / "how about 15 and 16 ?" | Correction: affordable units = all_counted_units (data dictionary); cells 11-14, 17-18 replaced |
| 13 | Step 4 — Cleaning | "done" (confirming Step 3) | Section 4: pre-integration cleaning of both datasets with cleaning log and validation |
| 14 | Full notebook | "now lets change the plan I need you to make the full notebook for me and send it ready ... highlight each decision ... make sure that we will get 100% of the grades ... revise it very carefully" | Sections 5-12 (integration, post-integration cleaning, validation, 12 RQs, story, contributions, prompts, decision register); decision callouts in all sections; full verification run |
| 15 | Explanation | "now can I understand a brief about every part ??" | Plain-language summary of every notebook section |
| 16 | Planning | "okay what left to do in this project" | Remaining deliverables: website, deployment, GitHub, README, submission |
| 17 | Website | "I already uploaded it and ran it ... and confirmed the contribution table" | Dash website (filters, search, Generate report, 5 charts, story), data preparation script, Render deployment files, README |
