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
The infrastructure team is shown collaboratively applying the systematic USE method checklist to troubleshoot a batch processing failure in the core banking system. A diagram visually supports this scene, depicting a flow of interconnected system components, each annotated with metrics for Utilization, Saturation, and Errors. Engineers are seen actively evaluating these metrics in a structured manner, highlighting bottlenecks and potential failure points. The visual emphasizes the organized progression of their analysis, revealing how each subsystem contributes to the overall troubleshooting process.
### Teaching Narrative
The USE Method provides a comprehensive framework for measuring resource health through three key dimensions: Utilization (how busy the resource is), Saturation (how much queueing is occurring), and Errors (failure counts). This systematic measurement approach ensures no resource constraints go unexamined, creating a methodical path through performance investigation. For banking infrastructure, USE metrics create a structured approach to identifying bottlenecks that might otherwise remain hidden during critical financial processing.
```markdown
### Common Example of the Problem

A bank's nightly batch reconciliation process has been gradually taking longer to complete, now threatening its 6 AM completion deadline before daily operations begin. The operations team has attempted various troubleshooting approaches, but without success. The following table summarizes their efforts:

| **Action Taken**                  | **Result**                                                                 | **Why It Failed**                                                                                       |
|-----------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Examined application logs         | Identified some non-critical errors but no clear root cause for the slowdown. | Focused only on the application layer, missing performance issues in underlying infrastructure.         |
| Increased server CPU and memory   | Observed no significant improvement in batch processing times.              | CPU and memory were not the bottleneck; resources were underutilized.                                  |
| Optimized database queries        | Minor performance gains, but reconciliation process still exceeded the deadline. | Query performance was not the primary constraint; the root issue lay in storage systems.               |

Without a systematic approach to resource measurement, the team concentrated on the most visible components while overlooking the actual constraint: disk I/O saturation on storage systems handling transaction journaling. By applying the USE methodology systematically to all resources, the team could identify the true bottleneck and address it effectively.
```
```markdown
### SRE Best Practice: Evidence-Based Investigation

Implement the USE method comprehensively across all system resources by following this checklist:

#### USE Method Checklist
1. **Inventory Resources:**
   - Compile a list of all system resources to evaluate, such as:
     - CPU
     - Memory
     - Network interfaces
     - Disk I/O
     - Storage capacity
     - File descriptors
     - Connection pools
     - Thread pools

2. **Measure Key Dimensions for Each Resource:**
   - **Utilization:** Determine the percentage of time the resource is busy (0-100%).
   - **Saturation:** Assess the extent of queued work that cannot be processed immediately.
   - **Errors:** Count the number of error events associated with the resource.

3. **Apply Consistent Measurement:**
   - Ensure all resources—both obvious and less apparent—are evaluated uniformly to avoid blind spots.

4. **Prioritize Examination:**
   - Focus on resources with the highest utilization or saturation first, as they are likely bottlenecks.

5. **Correlate Metrics with Application Performance:**
   - Map resource metrics to application behavior to pinpoint true constraints and their impact on performance.

#### Practical Example
By following systematic USE analysis, the team identified disk I/O saturation as the root cause of delayed write operations during high-volume journal processing. This bottleneck, overlooked by traditional monitoring, was causing severe performance degradation.
```
```markdown
### Banking Impact
For batch reconciliation processes, completion within defined windows directly impacts regulatory compliance and start-of-day operations. Missing this critical window is like a domino effect in motion: a single delay triggers a chain reaction of consequences throughout the organization. Branch openings may be delayed, customer account balances remain unupdated, financial reporting deadlines are missed, and regulatory submissions become late. Alternatively, it can be compared to a traffic jam on a major highway—when one lane slows down, the congestion builds and disrupts the flow for miles. The business impact extends beyond technical concerns, creating potential regulatory penalties, customer dissatisfaction from outdated information, and operational disruption across multiple departments. By addressing these bottlenecks with the USE Method, teams ensure smoother operations, preventing minor issues from snowballing into widespread chaos.
```
```markdown
### Implementation Guidance
1. Create a comprehensive resource inventory covering all infrastructure components.
2. Implement standardized USE dashboards for each resource type and instance.
3. Develop systematic troubleshooting runbooks that apply the USE methodology sequentially.
4. Establish baseline performance across all resources during normal operations.
5. Build automated analysis tools that flag anomalous USE metrics across the infrastructure:

```
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_use_metrics():
# Example: CPU Utilization
cpu_utilization = psutil.cpu_percent(interval=1)
if cpu_utilization > 85:
logging.warning(f"High CPU Utilization Detected: {cpu_utilization}%")


if __name__ == "__main__":
logging.info("Starting USE Metrics Analysis...")
analyze_use_metrics()
   ```

   This Python snippet demonstrates a basic automated tool leveraging the `psutil` library to monitor CPU utilization, memory saturation, and disk errors. Extend this logic to include additional resources and thresholds based on your infrastructure needs.
   ```
## Panel 2: The Invisible Bottleneck
```markdown
### Scene Description
The team uncovers disk I/O saturation during peak write periods, leading to nightly batch processing failures despite CPU and memory metrics appearing normal. To illustrate this issue, the scene includes a side-by-side comparison: on the left, dashboards showing healthy CPU and memory usage; on the right, a dashboard highlighting critical disk queue metrics with high saturation levels. This visual contrast emphasizes how standard metrics can obscure bottlenecks in less obvious system resources, making the problem tangible and easier to diagnose.
```
### Teaching Narrative
USE metrics reveal "invisible" resource constraints that standard monitoring approaches often miss but that significantly impact system performance. By measuring utilization, saturation, and errors for all system resources—not just the obvious ones—this methodology identifies non-intuitive bottlenecks that explain otherwise mysterious performance problems. For banking batch processing, comprehensive resource metrics enable precise identification of constraints that cause processing delays, reconciliation failures, or incomplete operations.
A core banking system performs end-of-day processing to calculate interest, update balances, and generate customer statements. Despite running on servers with ample CPU and memory capacity (both showing only 40-50% utilization), processing regularly fails to complete within its operational window. Traditional monitoring focuses exclusively on these primary resources, showing healthy systems with no apparent issues.

The root cause is uncovered using the USE methodology, which examines utilization, saturation, and errors across all resources. It reveals disk I/O saturation during peak write periods: operations are queuing for storage access despite low overall disk utilization. This saturation metric—indicating operations waiting in queue—was not being monitored at all, creating an invisible bottleneck that throttled the entire process.

#### Sequence of Events Diagram

Below is a timeline illustrating how this bottleneck manifests during nightly processing:

```plaintext
21:00 - Batch processing begins
       - Disk utilization at 20%, no issues detected

22:00 - Peak write period starts
       - Disk I/O saturation begins: operations queue for access
       - CPU and memory remain at 40-50% usage

23:00 - Queued disk operations grow
       - Processing delays accumulate

00:00 - Operational window ends
       - Batch processing incomplete due to unaddressed disk saturation
```

This timeline highlights the invisible nature of the bottleneck, as standard monitoring fails to capture the critical saturation metric. A simple dashboard addition to track disk queue lengths could have prevented these delays by enabling earlier intervention.
```markdown
### SRE Best Practice: Evidence-Based Investigation

Implement comprehensive resource measurement that captures oft-overlooked constraints. Use the following checklist to guide your evidence-based investigations:

#### Checklist for Evidence-Based Investigation
- [ ] **Expand Monitoring Scope**: Include all potential bottlenecks, not just primary resources like CPU and memory (e.g., disk I/O, network bandwidth, thread pools).
- [ ] **Measure Utilization and Saturation**: Track not only average utilization but also peak saturation levels for all critical resources.
- [ ] **Monitor Key Indicators**: Pay special attention to queue depths, wait times, and error rates as prime indicators of resource constraints.
- [ ] **Correlate with Workload Patterns**: Align observed resource saturation with specific workload patterns, schedules, or system events.
- [ ] **Characterize Workloads**: Break down resource demands by operation type (e.g., batch processing, real-time queries) to identify high-impact activities.

#### Case Study Snapshot
USE analysis of storage resources revealed a persistent bottleneck: 200+ operations queued for disk access during nightly statement generation. This critical issue was invisible in traditional utilization metrics but became evident when saturation and queue depth were analyzed. By applying the checklist, the root cause was identified, enabling targeted remediation.
```
```markdown
### Banking Impact

Invisible bottlenecks in financial batch processing have significant operational and regulatory repercussions. These issues can delay essential end-of-day tasks like interest calculations, statement generation, and balance updates, which are critical for ensuring seamless start-of-day operations. Such delays cascade into broader impacts, including ATM unavailability, inaccurate online banking data, and branch operational disruptions. Furthermore, prolonged processing times may breach regulatory requirements for system availability and completeness, introducing compliance risks alongside customer dissatisfaction.

| **Category**           | **Impact**                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------|
| **Operational**         | - Delayed end-of-day tasks (interest calculations, statement generation, balance updates).<br>- Disrupted start-of-day readiness (ATM downtime, online banking inaccuracies, branch delays). |
| **Customer Experience** | - Reduced ATM availability.<br>- Errors or delays in account balance and transaction accuracy.<br>- Poor online and in-branch banking experiences. |
| **Regulatory**          | - Breaches in reporting requirements for system availability.<br>- Non-compliance with processing window mandates.<br>- Increased scrutiny or penalties from regulatory bodies. |
```
```markdown
### Implementation Guidance

1. **Identify all storage resources in the banking architecture and implement queue monitoring:**  
   Use tools like `iostat` or modern observability platforms (e.g., Prometheus with node_exporter) to monitor disk I/O queues, ensuring visibility into saturation points.

2. **Create saturation-focused dashboards showing operation queuing across resources:**  
   Build dashboards that visualize queue depth, I/O utilization, and latency metrics. For example, in Grafana with Prometheus as a data source:  
```
   - title: Disk I/O Saturation
     panels:
       - type: graph
         title: Disk Queue Depth
         targets:
           - expr: node_disk_io_time_seconds_total{job="node_exporter"}
             legendFormat: '{{device}}'
             yaxes:
           - label: Queue Depth
             format: short
       - type: graph
         title: Disk Latency
         targets:
           - expr: rate(node_disk_io_time_seconds_total[1m]) / rate(node_disk_reads_completed_total[1m] + node_disk_writes_completed_total[1m])
             legendFormat: '{{device}}'
             yaxes:
           - label: Latency (s)
             format: s
   ```

   3. **Develop resource demand profiles for different batch operations:**  
   Analyze historical workload patterns to understand peak demand periods. For example, use tools like `pidstat` or APMs (Application Performance Monitoring tools) to correlate batch job characteristics with I/O resource consumption.

   4. **Implement I/O scheduling optimizations based on operation priority:**  
   Configure disk schedulers (e.g., `cfq` or `mq-deadline` on Linux) to prioritize critical batch operations. For example, adjust `ionice` settings:
   ```
ionice -c 1 -n 0 -p $(pgrep batch_processor)
   ```

   5. **Establish monitoring for all potential bottlenecks, not just traditional resource metrics:**  
   Expand monitoring to cover network throughput, database locks, and application thread pools. For example, integrate USE metrics into a centralized observability platform to ensure no resource bottleneck goes undetected.
   ```
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