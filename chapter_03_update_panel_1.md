# Chapter 3: Resource-Focused Measurement (USE Method)

## Chapter Overview: Resource-Focused Measurement (USE Method)

This chapter introduces the USE Method—Utilization, Saturation, and Errors—as a systematic framework for resource-level telemetry in complex systems. Moving beyond traditional CPU and memory monitoring, it uncovers how banking systems can experience severe failures due to overlooked resource constraints. From disk I/O saturation to connection pool exhaustion, the chapter presents real-world examples and structured practices that show why comprehensive resource visibility is essential. The chapter equips teams to map, measure, and monitor every layer of infrastructure and application architecture to find root causes before they escalate into business-impacting failures.

---

## Learning Objectives

By the end of this chapter, readers will be able to:

1. Define the three pillars of the USE Method: Utilization, Saturation, and Errors.
2. Apply USE methodology to all system resources—not just the obvious ones.
3. Detect hidden constraints using saturation metrics and queue depths.
4. Extend resource monitoring to application-level constraints (e.g., thread pools, connection limits).
5. Construct a measurement matrix that covers system layers from hardware to middleware.
6. Correlate constraints across components to identify cascading failures.
7. Prioritize root-cause bottlenecks over symptomatic performance issues.

---

## Key Takeaways

- **Most Problems Aren’t Where You’re Looking**: Just because your CPU isn’t on fire doesn’t mean everything’s fine. Bottlenecks are shy.
- **Saturation Is the Canary in the Coal Mine**: It tells you where queues are building, and where your next 3 AM page is coming from.
- **If It Can Queue, It Can Kill You**: Disk writes, DB connections, message queues—all innocent-looking until they clog up and ruin your batch window.
- **USE Your Head**: Stop staring at 40% CPU dashboards like they owe you answers. Build full resource inventories and measure everything.
- **Applications Have Bottlenecks Too**: Thread pools and connection pools need as much love (and scrutiny) as your servers.
- **The Matrix Is Real**: Build a measurement matrix so you can find blind spots before they find you.
- **Fix the Cause, Not the Echo**: Don’t throw memory at a queueing problem or scale your way out of a lock—you’ll just look busy while doing nothing useful.

---

## Panel 1: The Resource Detective
```markdown
### Scene Description
The infrastructure team is depicted in a collaborative troubleshooting session, systematically applying the USE method checklist to resolve a batch processing failure in the core banking system. The visual includes a diagram illustrating the structured evaluation process: a flowchart showing engineers analyzing each system component through three key dimensions—Utilization (resource activity levels), Saturation (queueing and waiting), and Errors (failure counts). Each step in the diagram highlights how metrics are gathered and assessed, emphasizing the methodical approach to uncovering performance bottlenecks. This combination of team interaction and visualized workflow brings clarity and engagement to the troubleshooting process.
```
### Teaching Narrative
The USE Method provides a comprehensive framework for measuring resource health through three key dimensions: Utilization (how busy the resource is), Saturation (how much queueing is occurring), and Errors (failure counts). This systematic measurement approach ensures no resource constraints go unexamined, creating a methodical path through performance investigation. For banking infrastructure, USE metrics create a structured approach to identifying bottlenecks that might otherwise remain hidden during critical financial processing.
```markdown
### Common Example of the Problem

A bank's nightly batch reconciliation process has been gradually taking longer to complete, now threatening its 6 AM completion deadline before daily operations begin. The operations team has tried various troubleshooting approaches, but without success. Here's a summary of their efforts and outcomes:

| Attempted Fix                     | Description                                                                 | Outcome                                                                                  |
|-----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Examining application logs        | Reviewed logs for errors or anomalies in batch processing.                  | No significant issues were identified, leading to further delays in pinpointing a cause. |
| Increasing server CPU and memory  | Upgraded CPU and memory resources on batch processing servers.              | No improvement in completion times, as the actual bottleneck was unrelated to compute.   |
| Optimizing database queries       | Tuned key database queries to improve execution efficiency.                 | Minimal impact on overall process time, as the database was not the primary bottleneck.  |

Without a systematic approach to resource measurement, the team focused on the most visible components and overlooked the actual constraint: disk I/O saturation on storage systems handling transaction journaling. Applying the USE methodology revealed this bottleneck by systematically evaluating utilization, saturation, and errors across all resources, ultimately leading to the resolution of the issue.
```
```markdown
### SRE Best Practice: Evidence-Based Investigation

Implement the USE method comprehensively across all system resources. Use the following checklist to guide your investigation:

#### USE Method Checklist:
1. **Inventory Resources**  
   - List all resources to examine, including:  
     - CPU  
     - Memory  
     - Network interfaces  
     - Disk I/O  
     - Storage capacity  
     - File descriptors  
     - Connection pools  
     - Thread pools  

2. **Measure Key Dimensions for Each Resource**  
   For every resource, collect metrics for the following dimensions:  
   - **Utilization**: Percentage of time the resource is busy (0-100%).  
   - **Saturation**: Extent of queued work that cannot be processed immediately.  
   - **Errors**: Count of error events related to the resource.

3. **Apply Consistent Measurement**  
   - Ensure all resources are measured systematically, not just the obvious ones.  

4. **Prioritize Investigation**  
   - Examine resources in order of highest utilization or saturation first.  

5. **Correlate Metrics with Application Performance**  
   - Align resource metrics with observed application behavior to identify true constraints.

#### Example Application:
Systematic USE analysis revealed disk I/O saturation causing write operations to queue during high-volume journal processing. This bottleneck, which severely impacted performance, went unnoticed by traditional monitoring alone.

By following this evidence-based checklist, you can systematically uncover resource constraints and address them with precision.
```
```markdown
### Banking Impact

Think of the batch reconciliation process as a factory assembly line producing a critical product: operational readiness for the next business day. Each step in the process is like a station on the assembly line, with dependencies that must complete in sequence. If one station—such as transaction matching or account updates—gets delayed, the entire line slows down or halts. Missing the "delivery deadline" (the reconciliation window) causes cascading disruptions: branches can't open on time, customer account balances stay outdated, and financial reports miss their regulatory deadlines.

Just as a factory delay can lead to inventory shortages, increased costs, or customer dissatisfaction, a delayed reconciliation process impacts the bank's operations and reputation. Regulatory penalties may arise from late submissions, customers may lose trust due to outdated account information, and internal teams face operational bottlenecks. By treating this process like a finely tuned assembly line, the importance of identifying and resolving resource constraints becomes clear: every component must operate efficiently to ensure smooth and timely delivery of business-critical outcomes.
```
```markdown
### Implementation Guidance
1. Create a comprehensive resource inventory covering all infrastructure components.
2. Implement standardized USE dashboards for each resource type and instance.
3. Develop systematic troubleshooting runbooks that apply USE methodology sequentially.
4. Establish baseline performance across all resources during normal operations.
5. Build automated analysis tools that flag anomalous USE metrics across the infrastructure.

#### Example: Automating USE Metric Analysis with Python
To streamline USE metric analysis, consider the following example using Python and Prometheus:

```
from prometheus_api_client import PrometheusConnect
import pandas as pd

# Connect to Prometheus
prom = PrometheusConnect(url="http://prometheus-server-url", disable_ssl=True)

# Define a function to query USE metrics
def query_use_metrics(resource, metric_type):
query = f'{metric_type}{{resource="{resource}"}}'
data = prom.get_current_metric_value(query=query)
return pd.DataFrame(data)

# Example: Fetch utilization, saturation, and error metrics for a given resource
resource_name = "batch_processing_node_1"
utilization = query_use_metrics(resource_name, "node_cpu_seconds_total")
saturation = query_use_metrics(resource_name, "node_load1")
errors = query_use_metrics(resource_name, "node_disk_io_time_seconds_total")

# Analyze and flag anomalies
def analyze_metrics(utilization, saturation, errors):
if utilization["value"].mean() > 0.8:
print(f"High Utilization Alert for {resource_name}")
if saturation["value"].mean() > 1:
print(f"Saturation Detected for {resource_name}")
if errors["value"].sum() > 0:
print(f"Error Events Found for {resource_name}")

analyze_metrics(utilization, saturation, errors)
```

This example demonstrates how to programmatically query and analyze USE metrics for a resource, enabling automated anomaly detection and alerting within your infrastructure. Extend this script to integrate with your monitoring stack and infrastructure-specific metrics.
```
## Panel 2: The Invisible Bottleneck
### Scene Description
Team discovering disk I/O saturation during peak write periods causing nightly batch processing failures despite normal CPU and memory metrics. Visual shows contrast between healthy CPU/memory dashboards and critical disk queue metrics.
### Teaching Narrative
USE metrics reveal "invisible" resource constraints that standard monitoring approaches often miss but that significantly impact system performance. By measuring utilization, saturation, and errors for all system resources—not just the obvious ones—this methodology identifies non-intuitive bottlenecks that explain otherwise mysterious performance problems. For banking batch processing, comprehensive resource metrics enable precise identification of constraints that cause processing delays, reconciliation failures, or incomplete operations.
### Common Example of the Problem
A core banking system performs end-of-day processing to calculate interest, update balances, and generate customer statements. Despite running on servers with ample CPU and memory capacity (both showing only 40-50% utilization), processing regularly fails to complete within its operational window. Traditional monitoring focuses exclusively on these primary resources, showing healthy systems with no apparent issues. USE methodology applied to all resources reveals the actual problem: disk I/O saturation during peak write periods, where operations are queuing for storage access despite low overall disk utilization. This saturation metric - showing operations waiting in queue - was not being monitored at all, creating an invisible bottleneck that throttled the entire process.
### SRE Best Practice: Evidence-Based Investigation
Implement comprehensive resource measurement that captures oft-overlooked constraints:

1. Expand monitoring beyond primary resources (CPU/memory) to include all potential bottlenecks
2. Measure both average utilization and peak saturation for all resources
3. Focus on queue depths and wait times as key indicators of constraint
4. Correlate resource saturation with specific workload patterns and timing
5. Use workload characterization to identify resource demands by operation type

USE analysis of storage resources reveals 200+ operations consistently queued for disk access during statement generation, creating a bottleneck that traditional utilization metrics completely missed.
### Banking Impact
In financial batch processing, invisible bottlenecks directly affect regulatory compliance and customer service. End-of-day processing failures delay interest calculations, statement generation, and balance updates critical for start-of-day operations. When these processes extend beyond their windows, they affect ATM availability, online banking accuracy, and branch readiness. Beyond operational impacts, these delays can trigger regulatory reporting requirements for system availability and processing completeness, creating compliance issues in addition to customer experience problems.
### Implementation Guidance
1. Identify all storage resources in the banking architecture and implement queue monitoring
2. Create saturation-focused dashboards showing operation queuing across resources
3. Develop resource demand profiles for different batch operations
4. Implement I/O scheduling optimizations based on operation priority
5. Establish monitoring for all potential bottlenecks, not just traditional resource metrics
## Panel 3: Beyond Basic Resources
### Scene Description
Advanced monitoring discussion with team identifying non-standard resources to measure: connection pools, thread pools, and queue depths in payment processing system. Visual shows resource hierarchy from physical to logical components.
### Teaching Narrative
Comprehensive USE measurement extends beyond traditional infrastructure metrics (CPU, memory, disk, network) to include application-level resources that often become critical constraints in banking systems. These expanded resource metrics include connection pools, thread pools, memory heap segments, buffer allocations, and query optimizers. By applying the USE methodology to these specialized resources, teams gain visibility into bottlenecks that traditional monitoring overlooks but that directly impact financial transaction processing.
### Common Example of the Problem
A payment processing platform handles credit card authorizations with consistent CPU and memory metrics well within capacity limits, yet transaction latency periodically spikes during peak periods. Traditional monitoring shows no resource constraints at the infrastructure level, creating confusion about the performance degradation. Expanded USE methodology reveals the actual bottleneck: database connection pool saturation where new authorization requests queue waiting for available connections, despite the database server itself showing only moderate load. This application-level resource constraint remained invisible to infrastructure-focused monitoring, yet directly impacted customer transaction times.
### SRE Best Practice: Evidence-Based Investigation
Implement expanded USE methodology that includes application-level resources:

1. Inventory all constrained resources in the application architecture:
   - Connection pools (database, API, service connections)
   - Thread pools (worker threads, asynchronous processing queues)
   - Memory structures (heap segments, buffer caches, in-memory data structures)
   - Locks and semaphores (database locks, file locks, shared resource controls)
   - Message queues (processing backlog, consumption rates, queue depths)
2. Measure utilization, saturation, and errors for each resource
3. Correlate application performance with resource constraints
4. Establish baseline patterns for normal vs. peak operations
5. Create early warning thresholds for approaching constraints

Comprehensive resource analysis reveals multiple constraint layers: connection pool saturation leading to thread pool exhaustion, creating cascading latency that traditional monitoring completely missed.
### Banking Impact
In payment authorization systems, application resource constraints directly impact transaction approval rates and processing times. Connection pool saturation creates authorization timeouts that may appear as technical declines to merchants and customers, potentially triggering unnecessary fraud alerts or transaction retries that compound the problem. These constraint-induced failures affect customer satisfaction, merchant relationships, and interchange revenue. For high-profile merchants or premium customers, these failures can damage strategic relationships beyond the immediate technical impact.
### Implementation Guidance
1. Create inventory of all application resource pools and their configuration limits
2. Implement comprehensive monitoring of connection acquisition times and queue depths
3. Develop dashboards showing pool utilization and saturation during different load profiles
4. Configure appropriate pool sizes based on actual usage patterns and transaction priorities
5. Establish graduated alerting for pool saturation with increasing urgency as constraints approach
## Panel 4: The Measurement Matrix
### Scene Description
Operations team creating comprehensive resource inventory with USE metrics applied to each component in trading platform. Visual shows structured matrix mapping resources to measurement types across system layers.
### Teaching Narrative
Systematic resource measurement requires a structured approach that inventories all potential constraints and applies consistent metrics across them. This resource measurement matrix applies USE metrics to physical resources (CPU, memory, network, disk), virtualization layers (hypervisor resources, container limits), middleware components (connection pools, caches, queues), and application resources (thread pools, handlers, buffers). For complex trading platforms, this comprehensive measurement approach ensures no potential bottleneck goes unmonitored.
### Common Example of the Problem
A trading platform experiences unpredictable performance degradation during market volatility, despite substantial infrastructure investment. The monitoring team tracks dozens of metrics but lacks a systematic approach to resource measurement. Some components have detailed monitoring while others have significant gaps. During incidents, the team wastes critical time checking resources ad hoc, with no clear methodology. A comprehensive USE measurement matrix reveals the problem: while most physical resources are well-monitored, virtualization layer metrics are completely missing, hiding CPU throttling at the hypervisor level that occurs during peak load but remains invisible to guest OS monitoring.
### SRE Best Practice: Evidence-Based Investigation
Implement a structured measurement matrix across all resource layers:

1. Create a two-dimensional matrix mapping:
   - Resource types (compute, memory, storage, network, pools, queues)
   - System layers (hardware, virtualization, OS, middleware, application)
2. For each cell in the matrix, implement appropriate USE metrics:
   - Utilization metrics appropriate to the resource type
   - Saturation measurements identifying queue depth or waiting
   - Error counters specific to each resource
3. Identify and address monitoring gaps in the matrix
4. Apply consistent measurement methodology across all resources
5. Establish cross-layer correlation to identify cascading constraints

Comprehensive measurement matrix reveals critical visibility gaps at the virtualization layer, explaining previously mysterious performance problems during peak trading periods.
### Banking Impact
For trading platforms, comprehensive resource visibility directly affects transaction execution quality and regulatory compliance. Invisible resource constraints can cause trade execution delays during market volatility—precisely when performance matters most—potentially costing clients significant amounts on price movements during delayed execution. These performance issues may also trigger regulatory reporting requirements for best execution compliance, creating both financial and regulatory consequences. Complete resource visibility enables the prioritization of critical trading operations even during constrained periods.
### Implementation Guidance
1. Develop a comprehensive resource inventory across all system layers
2. Create standardized USE metrics appropriate for each resource type
3. Implement monitoring to fill identified visibility gaps
4. Build cross-layer dashboards showing resource relationships
5. Establish regular reviews to identify and address measurement blind spots
## Panel 5: Correlating Resource Constraints
### Scene Description
Performance engineers mapping relationships between resource metrics to identify cascade patterns where one resource constraint triggers others. Visual shows dependency diagram highlighting how database connection limits impact thread pool utilization.
### Teaching Narrative
Advanced resource metrics reveal causal relationships between different system constraints, showing how saturation in one component can cascade to others. These correlation metrics map dependencies between resources, identify trigger thresholds where constraints begin to propagate, and measure amplification effects where small limitations in one area cause larger problems elsewhere. For banking systems, understanding these resource interaction patterns enables targeted optimization at constraint sources rather than just addressing symptoms.
### Common Example of the Problem
A bank's mobile deposit system experiences periodic processing delays despite having apparently adequate resources at each individual component. Engineers optimize each system in isolation based on its utilization metrics, but problems persist. Correlation analysis of resource metrics reveals the actual pattern: when image processing threads reach 70% utilization, database connections begin to be held longer, which then saturates the connection pool at 85% capacity, triggering a queue in the API gateway, ultimately causing end-user latency. Without understanding these cascade relationships, engineers focus on symptoms (API gateway queuing) rather than the root cause (image processing efficiency), implementing ineffective solutions that waste resources.
### SRE Best Practice: Evidence-Based Investigation
Implement resource correlation analysis that identifies dependency patterns:

1. Create resource dependency maps showing relationships between components
2. Measure correlation coefficients between different resource metrics
3. Identify threshold triggers where constraint in one resource affects others
4. Analyze propagation delays between related resource saturations
5. Determine amplification factors where small constraints cause larger downstream effects

Resource correlation analysis reveals that image processing thread saturation is the root cause of multiple downstream constraints, with clear timing signatures showing how problems cascade through the system.
### Banking Impact
In mobile deposit processing, understanding resource dependencies directly affects both customer experience and operational efficiency. Correlation metrics enable targeted optimization at constraint sources, reducing processing delays that affect funds availability and customer satisfaction. These insights also prevent wasteful overprovisioning of downstream resources that won't resolve the root constraint. For financial institutions, this analytical approach enables cost-effective reliability improvements by addressing actual bottlenecks rather than symptoms.
### Implementation Guidance
1. Create visualization tools that show resource metric correlations over time
2. Implement statistical analysis to identify significant metric relationships
3. Develop cascading constraint models for critical transaction paths
4. Build dependency-aware dashboards that highlight root constraints
5. Establish optimization priorities based on constraint impact analysis