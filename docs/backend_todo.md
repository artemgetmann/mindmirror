

✅ BACKEND TODOs (For MindMirror MK1)

We want to set a limit for how many members users can store on the free trial.

1. Memory Cap Enforcement
	•	✅ Cap memories per token at 25
	•	✅ Exclude admin_token from this limit
	•	✅ On store_memory, check count → if limit hit:
	•	Return error like:

{
  "error": "Memory limit reached. Upgrade to premium to store more.",
  "premium_link": "https://mindmirror.site/premium-waitlist"
}



⸻

2. Premium Waitlist Endpoint
	•	✅ Add new tool in the Claude-accessible API:

{
  "tool_name": "memory-system:join_waitlist",
  "params": {
    "email": "user@email.com"
  }
}


	•	✅ In backend: insert into waitlist_emails table in Supabase
	•	Schema: id, email, token_used, created_at

⸻

3. Return Limit Info via Claude
	•	✅ Modify Claude’s memory responses to display:
	•	Current count (X of 25 used)
	•	Include link when user hits limit:
“Looks like you’ve hit your memory limit. Join the premium waitlist here: [link]”

⸻

4. Admin Token Flag
	•	✅ Add column in Supabase tokens table:

is_admin BOOLEAN DEFAULT false


	•	✅ Skip memory limit + all restrictions if is_admin = true

⸻

5. Optional but Smart (needed for mk1 though?? i doubt it)
	•	✅ Log attempted writes after limit hit (rate of abuse tracking)
	•	Schema: id, token, attempted_memory_text, timestamp

⸻

6. Track: how many users hit memory_limit_reached = true
	•	Count how many unique emails sign up for premium waitlist
	•	we will Ship premium model the moment that crosses 15–30 

✳️ Summary Table

Feature	Status
Token memory limit	🔲 TODO
Admin token bypass	🔲 TODO
Join waitlist API	🔲 TODO
Claude integration w/ link	🔲 TODO
Abuse logging (optional)	🔲 Optional


2. front end Token Generation Page (or Modal) (this probably needs to be coordinated with the backend)

Upon clicking "Generate My Memory Token":

Display token clearly.

Display Claude-compatible URL clearly.

Concise setup instructions below token.

⸻
remove this document after these tasks are done 