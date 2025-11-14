# Comprehensive Guide to Modern AI Engineering Concepts

## Table of Contents
1. Machine Learning Fundamentals
2. Neural Networks and Deep Learning
3. Transformer Architecture and Attention
4. Large Language Models (LLMs)
5. Fine-Tuning Approaches
6. Retrieval-Augmented Generation (RAG)
7. AI Agents and Autonomous Systems
8. Prompt Engineering
9. Model Deployment and Production
10. Optimization Algorithms

---

## 1. Machine Learning Fundamentals

### What is Machine Learning?

Machine learning is a subset of artificial intelligence where systems learn patterns from data without being explicitly programmed. Instead of following predetermined rules, ML models identify relationships in data and use these patterns to make predictions or decisions on new, unseen data.

### The Machine Learning Pipeline

A machine learning pipeline is a series of interconnected data processing and modeling steps that streamlines working with ML models. A well-designed pipeline ensures reproducibility, efficiency, and reliability in producing ML solutions.

**Core Components of an ML Pipeline:**

1. **Data Collection**: Gathering raw data from various sources (databases, APIs, sensors)
2. **Data Preprocessing**: Cleaning and preparing data for analysis
3. **Feature Engineering**: Creating meaningful features from raw data
4. **Model Selection**: Choosing appropriate algorithms for the problem
5. **Model Training**: Teaching the model to recognize patterns
6. **Model Evaluation**: Assessing performance on validation/test data
7. **Deployment**: Moving the model to production environments
8. **Monitoring**: Tracking model performance and detecting drift

### Supervised vs. Unsupervised Learning

**Supervised Learning**: Learning from labeled data where each input has an associated correct answer. Used for classification (predicting categories) and regression (predicting continuous values).

**Unsupervised Learning**: Finding patterns in unlabeled data without predefined answers. Examples include clustering (grouping similar items) and dimensionality reduction.

---

## 2. Neural Networks and Deep Learning

### Neural Network Basics

A neural network is a machine learning architecture inspired by the structure of the human brain. It consists of interconnected nodes (neurons) organized in layers that process information through mathematical transformations.

### Architecture Components

**Input Layer**: Receives raw data features. Each neuron corresponds to one feature in the dataset.

**Hidden Layers**: Perform computational heavy lifting by applying transformations to inputs. These layers extract increasingly abstract representations of data. Deeper networks can capture more complex patterns but require more data and computation.

**Output Layer**: Produces final predictions. Format depends on task type (single value for regression, probabilities for classification, etc.).

### Forward Propagation

Forward propagation is how data moves through the network from input to output:

1. **Linear Transformation**: Each neuron receives inputs multiplied by learned weights, summed together, and bias is added
   - Formula: z = W·x + b (where W is weights, x is input, b is bias)

2. **Activation Function**: Non-linear transformation applied to the linear combination
   - Common activations: ReLU (Rectified Linear Unit), Sigmoid, Tanh
   - These non-linearities allow networks to learn complex relationships

3. **Signal Propagation**: Activated output becomes input to next layer

### Backpropagation and Learning

The backpropagation algorithm enables neural networks to learn by adjusting weights based on errors:

1. **Forward Pass**: Data flows through the network, producing predictions
2. **Loss Calculation**: Compare predictions to actual values using a loss function (e.g., Mean Squared Error, Cross-Entropy)
3. **Backward Pass**: Calculate how much each weight contributed to the error using the chain rule from calculus
4. **Weight Updates**: Adjust weights in direction that reduces loss

This iterative process—forward pass, loss calculation, backpropagation, weight update—repeats across many training examples until the model converges to an optimal solution.

### Activation Functions

**ReLU (Rectified Linear Unit)**: max(0, x)
- Most popular modern activation
- Computationally efficient
- Helps solve vanishing gradient problem

**Sigmoid**: 1/(1 + e^(-x))
- Outputs values between 0 and 1
- Useful for binary classification
- Can suffer from vanishing gradients

**Tanh**: (e^x - e^(-x))/(e^x + e^(-x))
- Outputs values between -1 and 1
- Similar to sigmoid but centered at 0

---

## 3. Transformer Architecture and Attention Mechanisms

### Why Transformers?

Traditional recurrent neural networks (RNNs) process sequences one element at a time, which limits parallelization and suffers from vanishing gradients on long sequences. Transformers solve this through parallel processing and attention mechanisms.

### The Attention Mechanism

Attention allows the model to focus on different parts of the input when making predictions. Core insight: each element should determine which other elements are important for understanding its meaning.

**Self-Attention Calculation**:

Each token (word/piece) needs three vectors:
- **Query (Q)**: "What am I looking for?"
- **Key (K)**: "What information do I have?"
- **Value (V)**: "What content should I pass on?"

The attention score for how much token i should attend to token j:

1. Compute similarity: score = Q·K^T / √(d_k)
   - Dot product measures relevance
   - Divided by √(d_k) for stability

2. Apply softmax: attention_weights = softmax(score)
   - Converts scores to probability distribution
   - Higher weights = more attention

3. Weighted sum: output = attention_weights · V
   - Creates context-aware representation

### Multi-Head Attention

Instead of single attention mechanism, use multiple attention heads simultaneously:

- Each head learns different aspects (syntax, semantics, position)
- Heads operate independently with their own Q, K, V projections
- Outputs concatenated and projected to final dimension
- Enables model to focus on multiple relationships at once

### Transformer Encoder and Decoder

**Encoder**: Processes input sequence bidirectionally
- Can attend to all tokens in sequence
- Produces context-aware representations

**Decoder**: Generates output sequence autoregressively (one token at a time)
- Masked self-attention prevents attending to future tokens
- Cross-attention to encoder output brings in context
- Generates predictions one step at a time

---

## 4. Large Language Models (LLMs)

### What Are LLMs?

Large language models are neural networks trained on massive amounts of text data to predict the next token (word piece) in a sequence. Despite their simplicity—predicting what comes next—this objective learns rich language understanding.

### Model Scaling

LLM capabilities emerge through scale across three dimensions:

1. **Data Scale**: Billions to trillions of tokens
2. **Model Scale**: Billions to hundreds of billions of parameters
3. **Compute Scale**: Massive distributed training infrastructure

Larger models show emergent abilities not present in smaller versions (few-shot learning, reasoning, tool use).

### Training Process

1. **Pre-training**: Unsupervised training on large text corpus
   - Learns fundamental language patterns
   - Often uses next-token prediction as objective
   - Takes weeks on expensive hardware

2. **Instruction Fine-tuning**: Supervised training on curated instruction-response pairs
   - Teaches model to follow commands
   - Improves quality and safety of responses
   - Much faster than pre-training

3. **RLHF (Reinforcement Learning from Human Feedback)**: Aligns model with human preferences
   - Incorporates human judgments about response quality
   - Trains reward model to predict human preferences
   - Fine-tunes model to maximize reward while staying close to original

### Token Prediction

At inference, models generate text token-by-token:

1. **Input Encoding**: Convert text to tokens
2. **Forward Pass**: Process through transformer layers
3. **Probability Distribution**: Output gives probability for each possible next token
4. **Sampling/Decoding**: Select next token (greedy, temperature-based, or nucleus sampling)
5. **Repeat**: New token becomes part of context for next prediction

---

## 5. Fine-Tuning Large Language Models

### Fine-Tuning Fundamentals

Fine-tuning adapts a pre-trained LLM to specific tasks or domains without training from scratch. This preserves learned knowledge while specializing the model.

### Types of Fine-Tuning

**Domain-Specific Fine-Tuning**:
- Adapts model to specialized domains (medical, legal, financial, technical)
- Requires domain-specific data (usually a few thousand examples)
- Improves accuracy in domain-specific terminology and concepts
- Example: Fine-tuning on medical papers for healthcare domain

**Instruction Fine-Tuning**:
- Teaches model to follow explicit instructions
- Uses instruction-response pairs: {"instruction": "...", "response": "..."}
- Improves ability to follow complex, multi-step directives
- Important for creating usable assistants

**Chat/Conversational Fine-Tuning**:
- Optimizes for multi-turn conversations
- Maintains context across exchanges
- Important for building chatbots and assistants

### Parameter-Efficient Fine-Tuning (PEFT)

Full fine-tuning updates all model parameters, which is computationally expensive. PEFT methods achieve 95% of full fine-tuning performance while reducing compute 70-80%.

**LoRA (Low-Rank Adaptation)**:
- Instead of updating weight matrix W, learn small matrices A and B
- Full update: W' = W + A·B^T
- Dramatically reduces parameters (1-3% of full model)
- Can stack multiple LoRA adapters
- Enables efficient multi-task learning

**QLoRA (Quantized LoRA)**:
- Combines LoRA with quantization (reducing precision of weights)
- 4-bit quantization reduces memory dramatically
- Enables fine-tuning on consumer GPUs
- Minimal performance loss vs. full fine-tuning

### Reinforcement Learning from Human Feedback (RLHF)

RLHF aligns model outputs with human preferences through a three-stage process:

**Stage 1: Collect Human Feedback**
- Generate multiple responses from model
- Human raters rank/score these responses
- Build preference dataset: (prompt, preferred_response, non_preferred_response)
- Diversity important—need examples covering various preference types

**Stage 2: Train Reward Model**
- Supervised learning on preference data
- Reward model learns to predict human preferences
- Input: (prompt, response) → Output: scalar reward score
- Typically a smaller model for efficiency

**Stage 3: Fine-tune LLM with Reward Model**
- Use Proximal Policy Optimization (PPO) algorithm
- Generate responses using current LLM
- Score with reward model
- Update LLM to maximize reward
- KL penalty keeps new model close to original (prevents reward hacking)

### Constitutional AI (CAI)

Alternative to RLHF that reduces human annotation burden:
- Define set of principles ("constitution") for desired behavior
- Use LLM with principles to critique responses
- LLM revises based on critique
- Reduces need for human raters while maintaining alignment

---

## 6. Retrieval-Augmented Generation (RAG)

### The RAG Problem

LLMs have fixed knowledge from training data and knowledge cutoff. For current information, proprietary data, or specialized domains, they hallucinate (generate false information). RAG solves this by connecting LLMs to external knowledge sources.

### RAG Architecture

**Three Components**:

1. **Knowledge Base/Vector Database**
   - Stores embeddings of source documents
   - Indexed for fast retrieval
   - Examples: Pinecone, Weaviate, Qdrant, ChromaDB

2. **Retriever**
   - Finds relevant documents for a query
   - Dense retrieval: embed query and find nearest embeddings (semantic search)
   - Sparse retrieval: keyword-based search (BM25)
   - Hybrid: combine both approaches

3. **Generator (LLM)**
   - Takes query + retrieved documents
   - Generates answer grounded in retrieved context
   - Produces more accurate, cited responses

### Implementation Steps

**Offline (Setup)**:
1. **Chunking**: Split documents into reasonable pieces (256-512 tokens)
   - Balance: too small = lost context, too large = mixed topics
   - Consider document structure (paragraphs, sections)

2. **Embedding**: Convert text chunks to vector embeddings
   - Use embedding model: OpenAI text-embedding-3, Cohere, open-source alternatives
   - Creates numerical representation of semantic meaning
   - Enables similarity calculations

3. **Indexing**: Store embeddings in vector database
   - Creates index for fast retrieval
   - Supports efficient similarity search

**At Runtime (Query)**:
1. **Embed Query**: Convert user query to same embedding space
2. **Retrieve**: Find top K most similar chunks (using cosine similarity or other distance metrics)
3. **Rerank**: (Optional) Use reranking model to order results by relevance
4. **Format**: Combine query + retrieved chunks into prompt
5. **Generate**: LLM produces answer based on context

### Advanced RAG Techniques

**Hybrid Search**: Combine vector + keyword search
- Vector search captures semantic meaning
- Keyword search captures exact matches
- Reranking combines and deduplicates results
- Better precision and recall than either alone

**Reranking**: Second-stage ranking after initial retrieval
- Initial retrieval fast but potentially noisy
- Reranking model (e.g., cross-encoder) scores top results
- Significantly improves answer quality

**Query Expansion**: Improve retrieval coverage
- Expand single query into multiple queries
- Retrieve results for each expanded query
- Handles query variations and aliases

**Metadata Filtering**: Pre-filter documents before semantic search
- Filter by source, date, category, etc.
- Reduces search space
- Improves relevance by domain-restricting

---

## 7. AI Agents and Autonomous Systems

### What Are AI Agents?

AI agents are autonomous systems that:
- **Perceive** their environment
- **Reason** about how to solve problems
- **Plan** multi-step solutions
- **Act** by using tools and making decisions
- **Learn** and adapt based on outcomes

Unlike simple Q&A systems, agents undertake complex workflows requiring multiple steps, tool usage, and dynamic decision-making.

### Agent Components

**Reasoning Engine**: 
- LLM that thinks through problems step-by-step
- Frameworks: ReAct (Reason + Act), Chain-of-Thought, Tree-of-Thoughts
- Plans approach before executing

**Tool Integration**:
- APIs (search, database queries, external services)
- Code execution (Python interpreter, database queries)
- Web access (browsing, information gathering)
- Domain-specific tools

**Memory Management**:
- Short-term: Current conversation context
- Long-term: Information stored for future reference
- Episodic: Record of past actions for learning

**Planning and Execution**:
1. Break complex task into subtasks
2. Plan execution order (sequential, parallel, conditional)
3. Execute tools in order
4. Monitor progress and adjust if needed

### Agent Patterns

**ReAct (Reason + Act)**:
- Alternates between thinking and action
- Structure: Thought → Action → Observation → Thought...
- Self-corrects when actions don't achieve goals
- Enables multi-step problem solving

**Tool-Use Pattern**:
- Agent decides which tool to use for each subtask
- Formats tool calls with appropriate parameters
- Processes results and plans next step
- Iterates until goal achieved

**Reflection Pattern**:
- Agent reviews its actions and outcomes
- Identifies failures or inefficiencies
- Adjusts strategy for future similar problems
- Enables learning from experience

### Orchestration and Safety

**Orchestration Layer**: 
- Manages workflow sequencing
- Enforces constraints and policies
- Handles error states and retries
- Ensures compliance with regulations

**Human-in-the-Loop**:
- Critical decisions require human approval
- Oversight mechanisms prevent harmful actions
- Human feedback improves agent performance

### Use Cases

- **Customer Support**: Handling inquiries, troubleshooting, escalating to humans
- **Supply Chain**: Optimization, inventory management, predictive maintenance
- **Software Engineering**: Code generation, debugging, testing
- **Research**: Literature review, experiment planning, result synthesis

---

## 8. Prompt Engineering

### Prompt Engineering Fundamentals

Prompt engineering is the art and science of designing inputs to guide AI models toward desired outputs. Small changes in phrasing can dramatically affect results.

### Prompting Strategies

**Zero-Shot Prompting**:
- Simple direct instruction without examples
- Model uses general knowledge
- Example: "Summarize this article: [text]"
- Works well for straightforward tasks

**One-Shot Prompting**:
- Provide single example of desired format/style
- Example: Shows one question-answer pair, then asks similar question
- Helps establish pattern

**Few-Shot Prompting**:
- Provide 3-5 diverse examples before the query
- Model learns format, style, patterns from examples
- More robust than zero-shot
- Especially effective for specific formats or complex reasoning
- Improves accuracy up to 28% on some tasks

**Chain-of-Thought (CoT) Prompting**:
- Instruct model to show reasoning steps
- Dramatically improves performance on logic/math problems
- Phrase: "Let's think step-by-step" or "First, let's break this down..."
- Can combine with few-shot (few-shot CoT is most effective)

**Few-Shot Chain-of-Thought**:
- Combine few-shot examples with step-by-step reasoning
- Each example includes both reasoning steps and final answer
- Most powerful combination for complex tasks

### Advanced Prompting Techniques

**Step-Back Prompting**:
- Generate high-level concepts before diving into details
- Helps with abstraction and pattern recognition
- Useful for complex multi-step problems

**Analogical Prompting**:
- Use analogies to explain concepts
- Model generates relevant examples and explanations
- Then applies to actual problem
- Leverages associative reasoning

**Tree-of-Thoughts**:
- Explore multiple reasoning paths
- Keep the most promising branches
- Backtrack if paths fail
- More thorough than linear CoT

**Self-Refining**:
- Generate initial response
- Ask model to critique its own response
- Iteratively improve based on critiques
- Reduces errors and improves quality

### Prompt Structure Best Practices

1. **Clear Instructions**: Specific, unambiguous commands
2. **Context**: Relevant background information
3. **Examples**: Demonstrations of desired format/quality
4. **Format Specification**: Exact desired output format
5. **Role Definition**: "Act as a [role]" can improve relevant outputs
6. **Constraints**: What not to do, limitations

### Avoiding Common Pitfalls

**Prompt Injection**:
- Malicious users craft inputs trying to override instructions
- Defense: Use separate variables for user input vs. system instructions
- Validate and sanitize user inputs

**Hallucination**:
- Model generates plausible-sounding but false information
- Mitigation: Combine with RAG for factual accuracy
- Ask model to cite sources

**Inconsistency**:
- Same prompt produces different outputs
- Temperature controls randomness (0=deterministic, 1=very random)
- Use lower temperature for consistency-critical applications

---

## 9. Model Deployment and Production Systems

### Why Deployment Matters

Many ML projects fail not due to models but deployment challenges. Production systems must handle:
- Continuous availability and uptime
- Variable request volumes
- Inference latency constraints
- Data quality changes over time
- Model accuracy degradation

### MLOps (Machine Learning Operations)

MLOps applies DevOps principles to ML, enabling:
- Reproducible ML pipelines
- Continuous integration/testing
- Continuous deployment
- Monitoring and alerting
- Automated retraining

### Containerization and Orchestration

**Docker Containers**:
- Package model + dependencies + runtime
- Ensures consistent behavior across environments
- Enables scaling and orchestration

**Kubernetes**:
- Orchestrate containers across multiple machines
- Handles scaling, failover, load balancing
- Manages resource allocation

### Deployment Patterns

**Batch Inference**:
- Process large volumes of data periodically
- Lower latency requirements
- Used for reports, offline predictions
- Example: Daily churn predictions

**Real-Time Inference (Online)**:
- Single request → single prediction
- Low latency requirements (milliseconds)
- Used for: API endpoints, interactive applications
- Requires scalable infrastructure

**Streaming**:
- Continuous data stream
- Process events as they arrive
- Used for: fraud detection, monitoring

### Model Monitoring and Observability

**Key Metrics**:

- **Latency**: Time to generate prediction (monitor for degradation)
- **Throughput**: Predictions per second
- **Error Rate**: Failed predictions or exceptions
- **Data Drift**: Input data distribution changes
- **Model Drift**: Model accuracy degradation over time

**Monitoring Tools**:
- Application Performance Monitoring (APM)
- Model-specific monitoring: Helicone, WhyLabs
- Dashboards for visualization and alerting

### Retraining and Updates

**Scheduled Retraining**:
- Retrain periodically (daily, weekly) on new data
- Captures evolving patterns
- Detects drift early

**Trigger-Based Retraining**:
- Monitor metrics, retrain when drift detected
- More efficient than scheduled
- Requires robust detection

**A/B Testing**:
- Deploy new model to subset of traffic
- Compare metrics vs. current model
- Gradual rollout reduces risk
- Enables data-driven decisions

---

## 10. Optimization Algorithms

### Gradient Descent Fundamentals

Gradient descent is the core algorithm for training neural networks. It iteratively adjusts weights in the direction that reduces loss.

**Update Rule**: w_new = w_old - α · ∇J(w)

Where:
- α = learning rate (controls step size)
- ∇J(w) = gradient (direction of steepest increase in loss)

Problem: Basic gradient descent converges slowly on complex problems.

### Optimization Algorithms

**Stochastic Gradient Descent (SGD)**:
- Updates weights using gradient from single sample (or small batch)
- Faster convergence than full-batch gradient descent
- More noisy updates can help escape local minima
- Still suffers from oscillations and slow convergence

**Momentum**:
- Maintains exponential moving average of gradients
- Accelerates convergence in consistent directions
- Reduces oscillations
- Equation: v = β·v_prev + ∇J(w), then w = w - α·v
- β typically 0.9

**AdaGrad (Adaptive Gradient)**:
- Adapts learning rate per parameter
- Parameters with large gradients get smaller learning rate
- Parameters with small gradients get larger learning rate
- Problem: Learning rate decreases over time, may stop learning

**RMSprop (Root Mean Square Propagation)**:
- Addresses AdaGrad's diminishing learning rate
- Maintains moving average of squared gradients
- Learning rate adapts but doesn't monotonically decrease
- Works well for many deep learning problems

**Adam (Adaptive Moment Estimation)**:
- Combines Momentum and RMSprop
- Maintains moving averages of both gradients and squared gradients
- Adaptive learning rate per parameter
- Bias correction ensures proper initialization
- Most widely used optimizer; good default choice
- Default hyperparameters work well across problems

**Comparison**:
- SGD: Simple, memory efficient, but slow
- Momentum: Faster convergence, still noisy
- RMSprop: Adaptive, stable, good for some problems
- Adam: Combines benefits of momentum and adaptive learning, most reliable

### Loss Functions

**Mean Squared Error (MSE)**:
- L = (1/n) · Σ(y_pred - y_true)²
- For regression tasks
- Sensitive to outliers

**Cross-Entropy Loss**:
- For classification tasks
- Measures difference between predicted and actual probability distributions
- Better for multi-class problems than MSE

**Huber Loss**:
- Combines MSE and Mean Absolute Error
- Less sensitive to outliers than MSE
- Useful for robust regression

### Learning Rate Selection

- **Too High**: Diverges, doesn't converge
- **Too Low**: Converges slowly, may get stuck
- **Just Right**: Good balance of speed and stability

**Strategies**:
- Learning rate schedules: Start high, decay over time
- Adaptive methods (Adam, RMSprop): Adjust automatically
- Warm-up: Start with small learning rate, increase gradually

---

## Practical Integration: Building End-to-End AI Systems

### A Typical Project Flow

1. **Problem Definition & Data Collection**
   - Define success metrics
   - Gather and explore data
   - Split into train/validation/test

2. **Data Preprocessing & Feature Engineering**
   - Handle missing values
   - Normalize/scale features
   - Create meaningful features
   - Address class imbalance if needed

3. **Model Selection & Training**
   - Choose appropriate architecture
   - Define loss function and optimizer
   - Train with monitoring
   - Validate on held-out data

4. **Fine-Tuning & Optimization**
   - Hyperparameter tuning
   - Early stopping to prevent overfitting
   - Consider domain-specific fine-tuning

5. **Evaluation & Analysis**
   - Test set evaluation
   - Error analysis
   - Fairness and bias assessment

6. **Deployment Preparation**
   - Containerize model
   - Create API interface
   - Set up monitoring

7. **Production Deployment**
   - Deploy to cloud or on-premises
   - Monitor performance
   - Set up retraining pipeline

8. **Continuous Improvement**
   - Collect production data
   - Monitor for drift
   - Periodic retraining
   - Gather feedback for next iteration

### Key Takeaways

- **Data is Everything**: Model quality fundamentally limited by data quality and quantity
- **Iteration is Critical**: ML development is iterative; rarely works first time
- **Monitor Constantly**: Production systems need continuous monitoring for issues
- **Automate Safely**: Automation increases efficiency but requires safeguards
- **Understand Your Tools**: Deep understanding beats memorizing frameworks
- **Balance Theory and Practice**: Theory guides principles, practice teaches reality
- **Stay Updated**: AI field evolves rapidly; continuous learning essential

---

## Glossary of Key Terms

**Embedding**: Numerical vector representation of text/data that captures semantic meaning

**Token**: Smallest unit processed by LLMs; roughly word piece (subword)

**Inference**: Using trained model to generate predictions on new data

**Hallucination**: LLM generating plausible but false information

**Overfitting**: Model memorizes training data, fails on new data

**Underfitting**: Model too simple to capture data patterns

**Epoch**: One complete pass through entire training dataset

**Batch**: Subset of training data used in single update

**Hyperparameter**: Setting that controls learning (learning rate, batch size, etc.)

**Activation Function**: Non-linear transformation applied to neuron outputs

**Gradient**: Direction and magnitude of loss increase with respect to parameters

**Loss Function**: Measure of prediction error; what we're trying to minimize

**Convergence**: When optimization algorithm reaches stable solution

**Cross-Validation**: Training multiple models on different data splits for robust evaluation

**Data Augmentation**: Creating variations of training examples to increase dataset size

**Feature Scaling**: Normalizing features to similar ranges

**Dimensionality Reduction**: Reducing number of features while preserving information

---

## Additional Resources for Deeper Learning

- **Neural Network Fundamentals**: Study backpropagation deeply—it's the foundation
- **Transformer Deep Dives**: Implement attention from scratch to understand it fully
- **LLM Capabilities**: Follow latest research on model scaling and emergence
- **Production ML**: Learn Docker, Kubernetes, and monitoring for real-world deployment
- **Domain Application**: Apply these concepts to specific domains (NLP, Vision, Recommendations)
- **Research Papers**: Read original papers (Attention Is All You Need, BERT, GPT papers) for depth
