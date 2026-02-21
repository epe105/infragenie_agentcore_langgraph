# InfraGenie Demo Talking Points

A guide for presenting InfraGenie demos effectively.

## Demo Overview

**What is InfraGenie?**
InfraGenie is a multi-agent AI system deployed on AWS AgentCore that automates infrastructure provisioning, security scanning, and remediation using Ansible Automation Platform and AWS services.

**Key Value Props:**
- 🤖 Multi-agent orchestration with LLM intelligence
- 🔧 Real infrastructure automation (not simulated)
- 🛡️ Security-first approach with compliance frameworks
- 🚀 Production-ready deployment on AWS AgentCore
- 🔄 Complete lifecycle: Provision → Secure → Validate

---

## Demo Setup

### Before the Demo

1. **Deploy agent:**
   ```bash
   agentcore deploy
   ```

2. **Verify deployment:**
   ```bash
   agentcore status
   ```

3. **Test connection:**
   ```bash
   python scripts/run_demo.py --query "Hello"
   ```

### Demo Environment

- **Deployed on:** AWS AgentCore
- **LLM:** Claude 3.5 Sonnet (AWS Bedrock)
- **Tools:** Ansible AAP + AWS Services
- **Execution:** All in cloud, no local dependencies

---

## Demo 1: Infrastructure Lifecycle (7 Agents)

### Opening

"Let me show you InfraGenie - a multi-agent system that orchestrates complete infrastructure lifecycles. This isn't a simulation - it's actually provisioning EC2 instances, creating S3 buckets, detecting security issues, and fixing them automatically."

### Run the Demo

```bash
python scripts/run_demo.py
# Select option 1
```

### What to Highlight

**1. Execution Log (as it appears):**

```
📋 EXECUTION LOG:
   🚀 [PROVISIONING AGENT] Starting EC2 provisioning via Ansible AAP...
```
"Notice the first agent - it's calling our Ansible Automation Platform to launch a job template. This is real infrastructure provisioning."

```
   💾 [STORAGE AGENT] Creating S3 bucket...
```
"The storage agent creates an S3 bucket. For demo purposes, we intentionally make it vulnerable by removing the public access block."

```
   🔍 [OBSERVABILITY AGENT] Scanning for security issues...
```
"The observability agent immediately detects the security issue - the bucket is publicly accessible."

```
   🛡️ [SECURITY AGENT] Validating findings and adding compliance context...
```
"The security agent validates this finding and adds compliance context from four frameworks: CIS, NIST, PCI DSS, and GDPR."

```
   📊 [ANALYSIS AGENT] Calculating risk scores...
```
"The analysis agent calculates a risk score out of 100, factoring in the severity and compliance violations."

```
   🔧 [REMEDIATION AGENT] Applying security fixes...
```
"The remediation agent automatically applies the fix - blocking public access on the bucket."

```
   🔍 [REFLECTION AGENT] Validating infrastructure and generating insights...
```
"Finally, the reflection agent validates everything worked and generates insights about what was accomplished."


**2. Summary Section:**

Point out the key metrics:
- "The risk score went from 100/100 (critical) to 10/100 (minimal) after remediation"
- "All four compliance frameworks were validated"
- "The entire process was autonomous - no manual intervention"

**3. Reflection & Insights:**

"The reflection agent doesn't just validate - it generates intelligent insights about what was accomplished and recommends next steps. This is where the LLM adds real value."

### Key Technical Points

1. **Multi-Agent Orchestration**
   - "Seven specialized agents, each with a specific responsibility"
   - "They pass state between each other using LangGraph"
   - "No single agent does everything - true separation of concerns"

2. **Real Infrastructure**
   - "This is calling actual Ansible Automation Platform job templates"
   - "Creating real S3 buckets in AWS"
   - "Not a simulation - you can see these resources in your AWS console"

3. **Security-First**
   - "Detects issues immediately after creation"
   - "Maps to compliance frameworks automatically"
   - "Remediates without human intervention"

4. **Production-Ready**
   - "Deployed on AWS AgentCore - same code for demos and production"
   - "Uses Claude 3.5 Sonnet via AWS Bedrock"
   - "OAuth-protected tool access"

---

## Demo 2: Security Scan (5 Agents)

### Opening

"Now let me show you the security scan workflow. This scans all your existing S3 buckets, finds vulnerabilities, and fixes them."

### Run the Demo

```bash
python scripts/run_demo.py
# Select option 2
```

### What to Highlight

**1. Scanning Phase:**
"The observability agent scans all S3 buckets in your account - not just one, but all of them."

**2. Findings:**
"It found X vulnerable buckets out of Y total. Each one is evaluated against our compliance frameworks."

**3. Remediation:**
"The remediation agent applies fixes to the most critical bucket first. In production, you could configure it to fix all of them."

**4. Reflection:**
"The reflection agent provides a summary of what was found, what was fixed, and what still needs attention."

### Key Technical Points

1. **Scalability**
   - "Scans all buckets, not just one"
   - "Prioritizes by risk score"
   - "Can be configured for batch remediation"

2. **Compliance**
   - "Maps findings to CIS, NIST, PCI DSS, GDPR"
   - "Provides audit trail"
   - "Generates documentation"

---

## Demo 3: Natural Language Query

### Opening

"InfraGenie isn't just for workflows - you can ask it anything about your infrastructure using natural language."

### Run the Demo

```bash
python scripts/run_demo.py
# Select option 3
# Ask: "List my Ansible inventories"
```

### What to Highlight

**1. Natural Language:**
"I just asked in plain English - no API calls, no CLI commands to remember."

**2. LLM Reasoning:**
"The LLM understands my intent, selects the right tool, and formats the response nicely."

**3. Tool Selection:**
"Behind the scenes, it called the Ansible MCP server's list_inventories tool."

### Example Queries

- "List my Ansible inventories"
- "Show me recent job executions"
- "What EC2 instances are running?"
- "Check the status of job 123"

---

## Cleanup Demo

### Show Cleanup

```bash
python scripts/cleanup_demo.py
# Select option 1 (clean all)
```

### What to Highlight

"The cleanup script also uses the agent - it launches the 'AWS - Delete VM' job template in Ansible AAP and removes the S3 buckets. Everything is automated."

---

## Q&A Preparation

### Common Questions

**Q: Is this really calling Ansible and AWS?**
A: "Yes! You can see the resources in your AWS console and the jobs in Ansible Automation Platform. This is real infrastructure automation."

**Q: How does it know what to do?**
A: "We use keyword detection to route to specialized workflows. If no keyword matches, the LLM reasons about what tools to use. Best of both worlds - fast routing for known patterns, flexible reasoning for everything else."

**Q: Can I add my own workflows?**
A: "Absolutely! You can create new workflows by defining agents and connecting them with LangGraph. The infrastructure lifecycle demo is a great template to start from."

**Q: What about security?**
A: "The Ansible MCP server uses OAuth authentication. AWS access is controlled by IAM roles. All secrets are managed through environment variables in AgentCore."

**Q: How much does this cost?**
A: "The LLM calls are minimal because we use keyword detection for routing. The workflows themselves don't use the LLM - they're deterministic. Most of the cost is the actual infrastructure resources you create."

**Q: Can this run in production?**
A: "Yes! It's deployed on AWS AgentCore, which is production-ready. You'd want to add more error handling, monitoring, and approval workflows, but the foundation is there."

---

## Demo Tips

### Do's

✅ Let the execution log scroll naturally - it shows the multi-agent orchestration  
✅ Point out the emojis - they make it easy to follow which agent is running  
✅ Highlight the reflection insights - that's where the LLM adds value  
✅ Show the cleanup - demonstrates the complete lifecycle  
✅ Mention compliance frameworks - CIS, NIST, PCI DSS, GDPR  

### Don'ts

❌ Don't skip the execution log - that's the key differentiator  
❌ Don't claim it's WCAG compliant - we can't validate that  
❌ Don't promise specific performance - it depends on AAP and AWS  
❌ Don't oversell the LLM - the workflows are deterministic by design  

---

## Closing

"InfraGenie demonstrates how multi-agent systems can automate complex infrastructure operations. It's not just about having an LLM - it's about orchestrating specialized agents, each doing one thing well, with the LLM providing intelligence where it matters most: understanding intent and generating insights."

**Call to Action:**
- "Try it yourself - the code is all here"
- "Extend it with your own workflows"
- "Deploy it to your own AgentCore instance"
- "Integrate it with your existing automation"
