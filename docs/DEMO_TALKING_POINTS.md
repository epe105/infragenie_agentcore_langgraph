# InfraGenie Demo Talking Points

A guide for presenting InfraGenie demos effectively.

## Demo Overview

**What is InfraGenie?**
InfraGenie is a multi-agent AI system deployed on AWS AgentCore that automates infrastructure provisioning, security scanning, and remediation. It features a main orchestrator agent (InfraGenieAgentCore) that intelligently routes user requests to specialized components: a planner component for creating execution plans, and workflow components (7-agent infrastructure lifecycle, 5-agent security scan) for executing real infrastructure operations using Ansible Automation Platform and AWS services.

**Architecture:**
```
InfraGenieAgentCore (Main Orchestrator)
├── PlannerAgent (Component) - Creates plans
├── Infrastructure Lifecycle (Component) - 7 agents execute
├── Security Scan (Component) - 5 agents execute
└── General Query (Fallback) - LLM with tools
```

**Key Value Props:**
- 💬 **Natural language interface** - Administrators speak conversationally (NEW!)
- 🤖 Multi-agent orchestration with LLM intelligence
- 📋 **System prompt-based planner** (Deep Agent Pattern)
- 👤 **Two-level approval workflow** (Strategic + Tactical)
- 🔧 Real infrastructure automation (not simulated)
- 🛡️ Security-first approach with compliance frameworks
- 🚀 Production-ready deployment on AWS AgentCore
- 🔄 Complete lifecycle: Plan → Provision → Secure → Validate

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
   python scripts/run_demo_interactive.py --query "Hello"
   ```

### Demo Environment

- **Deployed on:** AWS AgentCore
- **LLM:** Claude 3.5 Sonnet (AWS Bedrock)
- **Tools:** Ansible AAP + AWS Services
- **Execution:** All in cloud, no local dependencies

---

## Planner Demo: The "Deep Agent Pattern"

### Opening (SHOW THIS FIRST!)

"Before we run the full infrastructure lifecycle, let me show you something unique. InfraGenie has a main orchestrator agent that routes to different components. One component is the planner - and it's defined entirely in a system prompt, not code! This is called the 'deep agent pattern.'"

### The Magic Moment

**Show the system prompt file:**
```bash
cat src/planner_prompt.py
```

"See this? The entire planner 'tool' is just a system prompt. There's no `create_infrastructure_plan()` function in Python!"

### Run Planner Demo

```bash
agentcore invoke '{"prompt": "Create a plan for the infrastructure lifecycle demo"}'
```

### What to Highlight

**1. Plan Generation (10 seconds)**
```
📋 INFRASTRUCTURE PLAN

**Task:** Execute infrastructure lifecycle demo

**Explanation:**
[Plain language explanation appears here]

**Execution Steps:**
   1. [PROVISIONING] Create EC2 via Ansible AAP
      Tool: ansible_mcp | Duration: 3-5 minutes
   2. [STORAGE] Create S3 bucket
      Tool: aws_mcp | Duration: 30 seconds
   ...
```

"The LLM generated this entire plan - with 8 steps, time estimates, risk assessment, and cleanup instructions. And it did this in under 10 seconds because it doesn't need to load any MCP tools!"

**2. Key Points to Make:**
- ✅ "No planning code was written"
- ✅ "The tool is defined in the system prompt"
- ✅ "LLM generates plans dynamically"
- ✅ "Want to add a new field? Just edit the prompt!"
- ✅ "This is called the 'deep agent pattern'"

**3. Compare to Traditional:**
```
Traditional: 100+ lines of if/else planning logic
Deep Agent:  System prompt + 10 lines of parsing code
```

---

## Demo 1: Natural Language Prompts (NEW!)

### Opening

"Before we dive into the workflows, let me show you how administrators actually interact with InfraGenie. Instead of remembering specific commands, they can just speak naturally."

### Run the Demo

```bash
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
```

### What to Highlight

**1. Natural Language Input:**

"Notice I didn't have to say 'run the infrastructure lifecycle demo' - I just described what I want: provision a VM and an S3 bucket. That's how an administrator would naturally describe the task."

**2. Intelligent Detection:**

"Behind the scenes, InfraGenie looks for three things:
- An action word: provision, create, deploy, setup
- A compute resource: ec2, vm, instance
- A storage resource: s3, bucket, storage

When it sees all three, it knows to trigger the infrastructure lifecycle workflow."

**3. Examples that work:**
```
✅ "provision an ec2 vm and an s3 bucket"
✅ "create a vm and s3 storage"
✅ "deploy ec2 instance and bucket"
✅ "setup vm and s3"
```

"This flexibility means administrators don't need to memorize exact commands - they can describe tasks naturally."

---

## Demo 2: Infrastructure Lifecycle with Two-Level Approval

### Opening

"Now let's see what happens when we execute that request. InfraGenie has two approval gates - strategic and tactical. You approve the PLAN first, then approve specific REMEDIATIONS during execution."

### Alternative Opening

"Let me show you InfraGenie - a multi-agent system that orchestrates complete infrastructure lifecycles. This isn't a simulation - it's actually provisioning EC2 instances, creating S3 buckets, detecting security issues, and fixing them automatically."

### Run the Demo

```bash
python scripts/run_demo_interactive.py
# Select option 1: Infrastructure Lifecycle Demo
```

### What to Highlight

**1. Planning Phase (APPROVAL GATE #1):**

"First, the planner creates an execution plan..."

```
STEP 1: CREATING EXECUTION PLAN
⏳ Asking InfraGenie to create a plan...

📋 INFRASTRUCTURE PLAN
[Plan appears with 8 steps, time estimates, risks]

👤 Do you want to execute this plan? (yes/no):
```

"Notice the user sees EVERYTHING that will happen before execution starts. This is strategic approval - should we do this at all?"

[Type 'yes']

**2. Execution Phase:**

"Now the 7 execution agents take over..."

**3. Execution Log (as it appears):**

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

**4. Remediation Approval (APPROVAL GATE #2):**

"Now here's where it gets interesting - the workflow PAUSES and asks for specific approval..."

```
🚨 REMEDIATION APPROVAL REQUEST
======================================================================

📊 Infrastructure Context:
   • EC2 Instance: i-0123456789abcdef0
   • S3 Bucket: infragenie-backups-123

⚠️  Risk Score: 100/100

🔧 Proposed Remediation:
   • Action: Block all public access
   • Configuration: BlockPublicAcls, IgnorePublicAcls, etc.

📋 Compliance Frameworks:
   • CIS AWS Foundations: 2.1.5
   • NIST 800-53: AC-3
   • PCI DSS: 1.2.1
   • GDPR: Article 32

👤 Do you approve this remediation? (yes/no):
```

"This is tactical approval - granular control over specific actions. The user sees exactly what bucket, what action, and what compliance frameworks are involved."

[Type 'yes']

**5. Remediation Applied:**

```
   🔧 [REMEDIATION AGENT] Applying security fixes...
```
"The remediation agent applies the fix - blocking public access on the bucket."

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

1. **Main Orchestrator Architecture**
   - "InfraGenieAgentCore is the main orchestrator - it routes all user requests"
   - "It manages three types of components: planner, workflows, and general queries"
   - "The planner is a lightweight component that creates plans without executing"
   - "The workflows are execution components with 7 or 5 specialized agents"

2. **Multi-Agent Workflow Orchestration**
   - "Seven specialized agents in the infrastructure workflow, each with a specific responsibility"
   - "They pass state between each other using LangGraph"
   - "No single agent does everything - true separation of concerns"

3. **Real Infrastructure**
   - "This is calling actual Ansible Automation Platform job templates"
   - "Creating real S3 buckets in AWS"
   - "Not a simulation - you can see these resources in your AWS console"

4. **Security-First**
   - "Detects issues immediately after creation"
   - "Maps to compliance frameworks automatically"
   - "Remediates without human intervention"

5. **Production-Ready**
   - "Deployed on AWS AgentCore - same code for demos and production"
   - "Uses Claude 3.5 Sonnet via AWS Bedrock"
   - "OAuth-protected tool access"

---

## Demo 3: Security Scan (5 Agents)

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

## Demo 4: Natural Language Query

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
A: "We use intelligent keyword detection that's flexible enough for natural language. For example, it looks for combinations like 'provision' + 'ec2' + 's3' rather than exact phrases. This means administrators can describe tasks naturally without memorizing specific commands. If no keywords match, the LLM reasons about what tools to use. Best of both worlds - fast routing for known patterns, flexible reasoning for everything else."

**Q: Can I add my own workflows?**
A: "Absolutely! The main orchestrator (InfraGenieAgentCore) uses keyword detection to route to components. You can add new keywords and create new workflow components by defining agents and connecting them with LangGraph. The infrastructure lifecycle demo is a great template to start from. Just add your routing logic to the main orchestrator's process_message() method."

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

"InfraGenie demonstrates how a well-architected multi-agent system can automate complex infrastructure operations. The key is having a main orchestrator that intelligently routes requests to specialized components - a planner component for creating plans, workflow components with 7 or 5 specialized agents for execution, and a natural language interface that administrators can use conversationally. It's not just about having an LLM - it's about building the right architecture: a smart orchestrator that routes to focused components, with each component doing one thing well, and the LLM providing intelligence where it matters most: planning, understanding natural language intent, and generating actionable insights."

**Call to Action:**
- "Try it yourself - the code is all here"
- "Extend it with your own workflows"
- "Deploy it to your own AgentCore instance"
- "Integrate it with your existing automation"
