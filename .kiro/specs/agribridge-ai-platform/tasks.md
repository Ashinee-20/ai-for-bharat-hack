# Implementation Plan: AgriBridge AI Platform

## Overview

This implementation plan breaks down the AgriBridge AI platform into discrete, incremental coding tasks. The platform will be built using Python for AWS Lambda backend services, PostgreSQL for relational data, DynamoDB for NoSQL data, OpenSearch for vector search, and AWS Bedrock for LLM capabilities. The mobile application will use React Native with a quantized model for offline functionality.

The implementation follows a layered approach: infrastructure setup, core services, AI/ML integration, multi-channel interfaces, and testing. Each task builds on previous work to ensure continuous integration and validation.

## Tasks

- [x] 1. Set up project structure and infrastructure foundation
  - Create Python project with virtual environment and dependencies (boto3, fastapi, pydantic, psycopg2, opensearch-py)
  - Set up AWS CDK or Terraform infrastructure-as-code for Lambda, DynamoDB, RDS, OpenSearch, S3
  - Configure development environment with LocalStack for local AWS service emulation
  - Create shared utilities module for logging, error handling, and configuration
  - _Requirements: 15.1, 15.2_

- [ ] 2. Implement authentication service
  - [x] 2.1 Create user profile data models and DynamoDB table schemas
    - Define Pydantic models for FarmerProfile, BuyerProfile, and UserProfile
    - Create DynamoDB table with phone number hash as partition key
    - Implement phone number hashing utility with salt
    - _Requirements: 11.1, 11.2, 12.3_
  
  - [x] 2.2 Implement OTP generation and verification
    - Create OTP generation function (6-digit random code)
    - Integrate with AWS SNS for SMS sending
    - Implement OTP verification with 3-attempt limit and expiration
    - Generate JWT tokens upon successful verification
    - _Requirements: 11.4_
  
  - [ ]* 2.3 Write property test for OTP authentication flow
    - **Property 39: OTP Authentication Flow**
    - **Validates: Requirements 11.4**
  
  - [ ]* 2.4 Write unit tests for authentication edge cases
    - Test expired OTP rejection
    - Test invalid OTP with attempt limiting
    - Test JWT token generation and validation
    - _Requirements: 11.4_

- [ ] 3. Implement data encryption and security utilities
  - [-] 3.1 Create encryption utilities for data at rest
    - Implement AES-256 encryption/decryption functions using cryptography library
    - Create key management integration with AWS KMS
    - Add encryption wrappers for DynamoDB and RDS data
    - _Requirements: 12.1_
  
  - [ ]* 3.2 Write property test for encryption round-trip
    - **Property 40: Data Encryption at Rest**
    - **Validates: Requirements 12.1**
  
  - [~] 3.3 Configure TLS 1.3 for all API endpoints
    - Set up API Gateway with TLS 1.3 minimum
    - Configure Lambda function URLs with HTTPS only
    - _Requirements: 12.2_
  
  - [ ]* 3.4 Write property test for phone number hashing
    - **Property 42: Phone Number Hashing**
    - **Validates: Requirements 12.3**

- [ ] 4. Implement price service with mandi integration
  - [~] 4.1 Create price data models and DynamoDB schema
    - Define PriceData, TrendData, and Recommendation models
    - Create DynamoDB table with composite key (crop+district, date)
    - Set up TTL for 24-hour price cache expiration
    - _Requirements: 2.1, 2.2_
  
  - [~] 4.2 Implement external mandi API integration
    - Create HTTP client for government mandi APIs (Agmarknet)
    - Implement data fetching with error handling and retries
    - Parse and normalize mandi price data
    - _Requirements: 20.1_
  
  - [~] 4.3 Implement geospatial price query logic
    - Create function to calculate distance between coordinates
    - Implement nearest mandi search within radius
    - Sort results by distance and return top 3
    - _Requirements: 2.1_
  
  - [ ]* 4.4 Write property test for geospatial price query
    - **Property 4: Geospatial Price Query**
    - **Validates: Requirements 2.1**
  
  - [ ]* 4.5 Write property test for price data freshness
    - **Property 5: Price Data Freshness**
    - **Validates: Requirements 2.2**
  
  - [~] 4.6 Implement price trend analysis and forecasting
    - Create time-series analysis using exponential smoothing
    - Generate 7-day price forecasts with confidence intervals
    - Implement selling recommendation logic based on trends
    - _Requirements: 3.1, 3.3_
  
  - [ ]* 4.7 Write property test for historical price data range
    - **Property 8: Historical Price Data Range**
    - **Validates: Requirements 3.1**
  
  - [ ]* 4.8 Write property test for confidence score validity
    - **Property 9: Confidence Score Validity**
    - **Validates: Requirements 3.3**
  
  - [ ]* 4.9 Write property test for forecast disclaimer presence
    - **Property 10: Forecast Disclaimer Presence**
    - **Validates: Requirements 3.4**

- [ ] 5. Checkpoint - Ensure price service tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement buyer matching service with PostgreSQL
  - [~] 6.1 Set up PostgreSQL database with PostGIS extension
    - Create RDS PostgreSQL instance via infrastructure code
    - Enable PostGIS extension for geospatial queries
    - Create tables: buyers, crop_availability, matches, transactions
    - Set up indexes for geospatial and text search
    - _Requirements: 4.1, 4.2_
  
  - [~] 6.2 Implement crop availability registration
    - Create CropAvailability model with validation
    - Implement INSERT logic with geospatial data
    - Add image upload to S3 with URL storage
    - _Requirements: 4.1_
  
  - [ ]* 6.3 Write property test for crop registration data completeness
    - **Property 11: Crop Registration Data Completeness**
    - **Validates: Requirements 4.1**
  
  - [~] 6.4 Implement geospatial buyer-farmer matching
    - Create SQL query with PostGIS ST_DWithin for radius search
    - Filter by crop type, quality grade, and quantity
    - Calculate match scores based on distance and requirements
    - _Requirements: 4.2_
  
  - [ ]* 6.5 Write property test for geospatial buyer matching
    - **Property 12: Geospatial Buyer Matching**
    - **Validates: Requirements 4.2**
  
  - [~] 6.6 Implement consent-based contact sharing
    - Add farmer_consent field to matches table
    - Create logic to check consent before revealing contact info
    - _Requirements: 4.3, 12.4_
  
  - [ ]* 6.7 Write property test for consent-based contact sharing
    - **Property 13: Consent-Based Contact Sharing**
    - **Validates: Requirements 4.3, 12.4**
  
  - [~] 6.8 Implement rating system
    - Create transaction recording with ratings
    - Calculate average ratings from transaction history
    - Update buyer and farmer rating fields
    - _Requirements: 4.4_
  
  - [ ]* 6.9 Write property test for rating calculation accuracy
    - **Property 14: Rating Calculation Accuracy**
    - **Validates: Requirements 4.4**

- [ ] 7. Implement RAG engine with OpenSearch
  - [~] 7.1 Set up OpenSearch cluster and index
    - Create OpenSearch domain via infrastructure code
    - Define index mapping with knn_vector field for embeddings
    - Configure HNSW algorithm for vector similarity search
    - _Requirements: 16.1, 16.2_
  
  - [~] 7.2 Implement document embedding and indexing
    - Integrate with AWS Bedrock Titan Embeddings model
    - Create batch embedding function for agricultural documents
    - Implement document indexing with metadata
    - Load initial 10,000+ advisory documents
    - _Requirements: 16.1_
  
  - [~] 7.3 Implement semantic search and retrieval
    - Create query embedding function
    - Implement k-NN search to retrieve top 5 documents
    - Return documents with relevance scores
    - _Requirements: 16.2_
  
  - [ ]* 7.4 Write property test for RAG top-K retrieval
    - **Property 50: RAG Top-K Retrieval**
    - **Validates: Requirements 16.2**
  
  - [~] 7.5 Implement confidence-based uncertainty indication
    - Calculate average relevance score from retrieved documents
    - Add uncertainty disclaimer when confidence < 70%
    - _Requirements: 16.5_
  
  - [ ]* 7.6 Write property test for RAG confidence indication
    - **Property 51: RAG Confidence Indication**
    - **Validates: Requirements 16.5**

- [ ] 8. Implement LLM integration with AWS Bedrock
  - [~] 8.1 Create Bedrock client and prompt templates
    - Initialize boto3 Bedrock runtime client
    - Create prompt templates for different intents (price, advisory, matching)
    - Implement prompt formatting with RAG context injection
    - _Requirements: 7.1, 7.2_
  
  - [~] 8.2 Implement intent classification
    - Create classification prompt with few-shot examples
    - Parse LLM response to extract intent enum
    - Handle ambiguous queries with clarification requests
    - _Requirements: 7.1, 7.4_
  
  - [ ]* 8.3 Write property test for intent classification accuracy
    - **Property 23: Intent Classification Accuracy**
    - **Validates: Requirements 7.1**
  
  - [ ]* 8.4 Write property test for ambiguous query clarification
    - **Property 25: Ambiguous Query Clarification**
    - **Validates: Requirements 7.4**
  
  - [~] 8.5 Implement conversation context management
    - Store conversation history in DynamoDB with TTL
    - Include last 5 turns in LLM prompt
    - Implement context summarization for long conversations
    - _Requirements: 7.3_
  
  - [ ]* 8.6 Write property test for conversation context maintenance
    - **Property 24: Conversation Context Maintenance**
    - **Validates: Requirements 7.3**
  
  - [~] 8.7 Implement multilingual support
    - Add language parameter to all LLM calls
    - Create language-specific prompt templates
    - Implement agricultural entity recognition for regional terms
    - _Requirements: 1.5, 7.5, 18.1_
  
  - [ ]* 8.8 Write property test for agricultural entity recognition
    - **Property 26: Agricultural Entity Recognition**
    - **Validates: Requirements 7.5**

- [ ] 9. Checkpoint - Ensure AI/ML services tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement advisory service
  - [~] 10.1 Create advisory service with RAG integration
    - Implement getCropAdvisory function using RAG retrieval
    - Implement getFertilizerRecommendation with context augmentation
    - Integrate weather API for weather-based advice
    - _Requirements: 5.1, 5.2, 5.3, 20.2_
  
  - [ ]* 10.2 Write property test for RAG document retrieval
    - **Property 15: RAG Document Retrieval**
    - **Validates: Requirements 5.3**
  
  - [~] 10.3 Implement language consistency for advisory
    - Ensure advisory responses match user's language preference
    - Translate technical terms appropriately
    - _Requirements: 5.4_
  
  - [ ]* 10.4 Write property test for advisory language consistency
    - **Property 3: Language Preference Persistence** (covers advisory)
    - **Validates: Requirements 5.4**

- [ ] 11. Implement query router service
  - [~] 11.1 Create query router with intent-based routing
    - Implement routeQuery function that classifies intent
    - Route to appropriate service (price, matching, advisory)
    - Handle multi-turn conversations with session management
    - _Requirements: 1.1, 1.2, 1.3, 7.1_
  
  - [~] 11.2 Implement comprehensive interaction logging
    - Log all queries with channel, intent, response time
    - Store logs in DynamoDB with GSI for analytics
    - Include error logging with context
    - _Requirements: 14.1, 19.5, 20.5_
  
  - [ ]* 11.3 Write property test for comprehensive interaction logging
    - **Property 47: Comprehensive Interaction Logging**
    - **Validates: Requirements 14.1, 19.5, 20.5**
  
  - [~] 11.4 Implement API response completeness validation
    - Create response validators for all service responses
    - Ensure all required fields are present and non-null
    - _Requirements: 2.5, 4.5, 13.5_
  
  - [ ]* 11.5 Write property test for API response completeness
    - **Property 7: API Response Completeness**
    - **Validates: Requirements 2.5, 4.5, 13.5**

- [ ] 12. Implement SMS gateway service
  - [~] 12.1 Create SMS gateway with AWS SNS integration
    - Implement receiveMessage handler for incoming SMS
    - Implement sendMessage function with SNS
    - Handle message splitting for >160 characters
    - _Requirements: 1.2, 10.1, 10.3_
  
  - [ ]* 12.2 Write property test for SMS message routing
    - **Property 1: SMS Message Routing**
    - **Validates: Requirements 1.2**
  
  - [~] 12.3 Implement SMS command parsing
    - Create parser for structured commands (PRICE WHEAT DELHI)
    - Fallback to LLM for natural language SMS
    - _Requirements: 10.2_
  
  - [ ]* 12.4 Write property test for SMS format flexibility
    - **Property 33: SMS Format Flexibility**
    - **Validates: Requirements 10.2**
  
  - [ ]* 12.5 Write property test for SMS message splitting
    - **Property 34: SMS Message Splitting**
    - **Validates: Requirements 10.3**
  
  - [~] 12.6 Implement SMS rate limiting
    - Create DynamoDB counter for queries per farmer per day
    - Enforce 10 query limit with appropriate error message
    - _Requirements: 10.5_
  
  - [ ]* 12.7 Write property test for SMS rate limiting
    - **Property 36: SMS Rate Limiting**
    - **Validates: Requirements 10.5**
  
  - [ ]* 12.8 Write property test for SMS delivery confirmation
    - **Property 35: SMS Delivery Confirmation**
    - **Validates: Requirements 10.4**

- [ ] 13. Implement IVR telephony integration
  - [~] 13.1 Set up telephony provider integration (Twilio/Exotel)
    - Create webhook handlers for incoming calls
    - Implement DTMF menu navigation
    - Set up call routing and session management
    - _Requirements: 9.1, 9.5_
  
  - [ ]* 13.2 Write property test for multi-modal IVR input support
    - **Property 27: Multi-Modal IVR Input Support**
    - **Validates: Requirements 9.1**
  
  - [~] 13.3 Implement voice-to-text with AWS Transcribe
    - Integrate AWS Transcribe for speech recognition
    - Support multiple Indian languages
    - Handle audio streaming and real-time transcription
    - _Requirements: 9.2_
  
  - [ ]* 13.4 Write property test for voice-to-text conversion
    - **Property 28: Voice-to-Text Conversion**
    - **Validates: Requirements 9.2**
  
  - [~] 13.5 Implement text-to-speech with AWS Polly
    - Integrate AWS Polly for speech synthesis
    - Support regional Indian language voices
    - Ensure language consistency with user preference
    - _Requirements: 9.3_
  
  - [ ]* 13.6 Write property test for text-to-speech language consistency
    - **Property 29: Text-to-Speech Language Consistency**
    - **Validates: Requirements 9.3**
  
  - [~] 13.7 Implement call recording with consent
    - Add consent collection in IVR flow
    - Enable recording only when consent is granted
    - Store recordings in S3 with encryption
    - _Requirements: 9.4_
  
  - [ ]* 13.8 Write property test for consent-based call recording
    - **Property 30: Consent-Based Call Recording**
    - **Validates: Requirements 9.4**
  
  - [ ]* 13.9 Write property test for call queue management
    - **Property 31: Call Queue Management**
    - **Validates: Requirements 9.5**

- [ ] 14. Checkpoint - Ensure multi-channel services tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implement mobile app sync service
  - [~] 15.1 Create sync service with delta synchronization
    - Implement syncUp to receive device changes
    - Implement syncDown to send server updates
    - Use timestamp-based delta sync to minimize data transfer
    - _Requirements: 8.3_
  
  - [ ]* 15.2 Write property test for delta synchronization
    - **Property 20: Delta Synchronization**
    - **Validates: Requirements 8.3**
  
  - [~] 15.3 Implement sync prioritization
    - Prioritize critical data (prices, buyer matches) over advisory
    - Implement priority queue for sync operations
    - _Requirements: 8.2_
  
  - [ ]* 15.4 Write property test for sync data prioritization
    - **Property 19: Sync Data Prioritization**
    - **Validates: Requirements 8.2**
  
  - [~] 15.5 Implement sync retry with exponential backoff
    - Add retry logic with exponential delays (1s, 2s, 4s)
    - Limit to 3 retry attempts
    - _Requirements: 8.4_
  
  - [ ]* 15.6 Write property test for sync retry with exponential backoff
    - **Property 21: Sync Retry with Exponential Backoff**
    - **Validates: Requirements 8.4**
  
  - [~] 15.7 Implement conflict resolution
    - Use last-write-wins strategy with timestamps
    - Log conflicts for manual review if needed
    - _Requirements: 6.4_
  
  - [ ]* 15.8 Write property test for automatic sync initiation
    - **Property 18: Automatic Sync Initiation**
    - **Validates: Requirements 6.4, 8.1**

- [ ] 16. Implement mobile application (React Native)
  - [~] 16.1 Set up React Native project with offline-first architecture
    - Initialize React Native project with TypeScript
    - Set up SQLite for local caching
    - Configure AsyncStorage for app state
    - _Requirements: 1.3, 6.1_
  
  - [~] 16.2 Implement offline data caching
    - Create SQLite schema for cached prices, advisory, queries
    - Implement cache population on app install
    - Add cache invalidation logic
    - _Requirements: 6.1, 6.3_
  
  - [ ]* 16.3 Write property test for offline app launch
    - **Property 2: Offline App Launch**
    - **Validates: Requirements 1.3, 6.1**
  
  - [ ]* 16.4 Write property test for offline data persistence
    - **Property 17: Offline Data Persistence**
    - **Validates: Requirements 6.3**
  
  - [~] 16.5 Integrate quantized LLM for offline inference
    - Download and integrate quantized Llama 2 7B model (~500MB)
    - Implement local inference using ONNX Runtime or llama.cpp
    - Create fallback to cloud when model cannot answer
    - _Requirements: 17.1, 17.5_
  
  - [ ]* 16.6 Write property test for offline query processing
    - **Property 16: Offline Query Processing**
    - **Validates: Requirements 6.2, 5.5**
  
  - [ ]* 16.7 Write property test for offline query queuing
    - **Property 53: Offline Query Queuing**
    - **Validates: Requirements 17.5**
  
  - [~] 16.8 Implement UI with offline/sync status indicators
    - Create status bar showing offline/online/syncing state
    - Display last successful sync timestamp
    - Add visual indicators for data staleness
    - _Requirements: 6.5, 8.5_
  
  - [ ]* 16.9 Write property test for offline and sync status display
    - **Property 22: Offline and Sync Status Display**
    - **Validates: Requirements 6.5, 8.5**
  
  - [~] 16.10 Implement language selection and persistence
    - Create language picker UI
    - Store language preference locally and sync to cloud
    - Apply language to all UI elements
    - _Requirements: 1.4, 18.3_
  
  - [ ]* 16.11 Write property test for language preference persistence
    - **Property 3: Language Preference Persistence**
    - **Validates: Requirements 1.4, 18.3**
  
  - [~] 16.12 Implement crash recovery
    - Add error boundary components
    - Persist app state before crash
    - Restore state on app restart
    - _Requirements: 19.3_
  
  - [ ]* 16.13 Write property test for mobile app crash recovery
    - **Property 57: Mobile App Crash Recovery**
    - **Validates: Requirements 19.3**

- [ ] 17. Implement error handling and fallback mechanisms
  - [~] 17.1 Create LLM failure fallback handler
    - Detect LLM timeouts and errors
    - Return fallback response with support contact
    - _Requirements: 19.1_
  
  - [ ]* 17.2 Write property test for LLM failure fallback
    - **Property 55: LLM Failure Fallback**
    - **Validates: Requirements 19.1**
  
  - [~] 17.3 Implement price data unavailability handling
    - Return last known prices with timestamp
    - Add staleness warning to response
    - _Requirements: 19.2_
  
  - [ ]* 17.4 Write property test for price data unavailability handling
    - **Property 56: Price Data Unavailability Handling**
    - **Validates: Requirements 19.2**
  
  - [~] 17.5 Implement external API fallback
    - Detect API failures for mandi and weather services
    - Use cached data with staleness indicator
    - _Requirements: 20.3_
  
  - [ ]* 17.6 Write property test for external API fallback
    - **Property 58: External API Fallback**
    - **Validates: Requirements 20.3**
  
  - [~] 17.7 Implement external data validation
    - Validate price data for anomalies (negative, extreme outliers)
    - Flag suspicious data for review
    - _Requirements: 20.4_
  
  - [ ]* 17.8 Write property test for external data validation
    - **Property 59: External Data Validation**
    - **Validates: Requirements 20.4**

- [ ] 18. Implement analytics and reporting
  - [~] 18.1 Create analytics aggregation functions
    - Aggregate query logs by crop, region, channel
    - Calculate buyer-farmer match rates
    - Compute transaction completion rates
    - _Requirements: 14.2, 14.5_
  
  - [ ]* 18.2 Write property test for transaction tracking
    - **Property 48: Transaction Tracking**
    - **Validates: Requirements 14.2**
  
  - [ ]* 18.3 Write property test for adoption metrics calculation
    - **Property 49: Adoption Metrics Calculation**
    - **Validates: Requirements 14.5**

- [ ] 19. Implement buyer-specific features
  - [~] 19.1 Create buyer registration and profile management
    - Implement buyer registration with business details
    - Store crop interests and purchase capacity
    - _Requirements: 13.1_
  
  - [ ]* 19.2 Write property test for buyer registration data collection
    - **Property 44: Buyer Registration Data Collection**
    - **Validates: Requirements 13.1**
  
  - [~] 19.3 Implement buyer search with quality filtering
    - Create search function with quality grade filters
    - Return only matching results
    - _Requirements: 13.3_
  
  - [ ]* 19.4 Write property test for buyer search quality filtering
    - **Property 45: Buyer Search Quality Filtering**
    - **Validates: Requirements 13.3**
  
  - [~] 19.5 Implement buyer favorites functionality
    - Create favorites table/collection
    - Add/remove favorite farmers
    - Retrieve favorites list
    - _Requirements: 13.4_
  
  - [ ]* 19.6 Write property test for buyer favorites management
    - **Property 46: Buyer Favorites Management**
    - **Validates: Requirements 13.4**

- [ ] 20. Implement data privacy and compliance features
  - [~] 20.1 Create data deletion handler
    - Implement deletion across all storage systems (DynamoDB, RDS, S3)
    - Verify complete data removal
    - _Requirements: 12.5_
  
  - [ ]* 20.2 Write property test for data deletion on request
    - **Property 43: Data Deletion on Request**
    - **Validates: Requirements 12.5**
  
  - [~] 20.2 Implement profile data validation and sync
    - Validate profile updates against schema
    - Sync profile changes across all channels
    - _Requirements: 11.3_
  
  - [ ]* 20.3 Write property test for profile data validation and sync
    - **Property 38: Profile Data Validation and Sync**
    - **Validates: Requirements 11.3**

- [ ] 21. Implement remaining property tests for comprehensive coverage
  - [ ]* 21.1 Write property test for offline price cache display
    - **Property 6: Offline Price Cache Display**
    - **Validates: Requirements 2.3**
  
  - [ ]* 21.2 Write property test for profile creation on first use
    - **Property 37: Profile Creation on First Use**
    - **Validates: Requirements 11.1**
  
  - [ ]* 21.3 Write property test for data encryption in transit
    - **Property 41: Data Encryption in Transit**
    - **Validates: Requirements 12.2**
  
  - [ ]* 21.4 Write property test for quantized model language parity
    - **Property 52: Quantized Model Language Parity**
    - **Validates: Requirements 17.4**
  
  - [ ]* 21.5 Write property test for crop name bilingual display
    - **Property 54: Crop Name Bilingual Display**
    - **Validates: Requirements 18.5**
  
  - [ ]* 21.6 Write property test for SMS price query processing
    - **Property 32: SMS Price Query Processing**
    - **Validates: Requirements 10.1**

- [ ] 22. Integration and end-to-end wiring
  - [~] 22.1 Wire all Lambda functions to API Gateway
    - Create API Gateway routes for all services
    - Configure Lambda integrations with proper IAM roles
    - Set up request/response transformations
    - _Requirements: All_
  
  - [~] 22.2 Configure CloudWatch logging and monitoring
    - Set up log groups for all Lambda functions
    - Create CloudWatch dashboards for key metrics
    - Configure alarms for error rates and latency
    - _Requirements: 14.1, 15.3_
  
  - [~] 22.3 Set up CI/CD pipeline
    - Create GitHub Actions or AWS CodePipeline workflow
    - Automate testing, building, and deployment
    - Configure staging and production environments
    - _Requirements: 15.2_
  
  - [ ]* 22.4 Write integration tests for end-to-end flows
    - Test complete farmer query flow (IVR → LLM → Response)
    - Test buyer-farmer matching flow
    - Test offline-to-online sync flow
    - _Requirements: All_

- [ ] 23. Final checkpoint - Comprehensive testing and validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all 59 correctness properties have corresponding property tests
  - Run load tests to validate performance requirements
  - Conduct security audit of authentication and data protection

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests should run minimum 100 iterations with realistic Indian agricultural data
- Use fast-check (TypeScript) or Hypothesis (Python) for property-based testing
- Mobile app can be built separately by a mobile team using the provided API specifications
- Infrastructure setup (Task 1) should be completed before other tasks
- Checkpoints ensure incremental validation at major milestones
