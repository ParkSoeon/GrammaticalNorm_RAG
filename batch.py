    # RAG 시스템 초기화
    rag_system = KoreanRAGSystem(model_name=args.model_name)
    
    # 청크 로드
    if os.path.exists(args.chunk_file):
        rag_system.load_chunks(args.chunk_file)
    else:
        print(f"Chunk file not found: {args.chunk_file}")
        print("Please run chunk.py first to create chunks")
        return
    
    if args.mode == 'test':
        # 테스트 모드 - 단일 질문 처리
        while True:
            question = input("\n질문을 입력하세요 (종료: quit): ")
            if question.lower() == 'quit':
                break
            
            question_type = input("문제 유형 (선택형/교정형/기타): ")
            if not question_type:
                question_type = "기타"
            
            print("\n처리 중...")
            answer = rag_system.process_question(question, question_type)
            print(f"\n답변:\n{answer}")
    
    elif args.mode == 'submit':
        # 제출 모드 - 배치 처리
        if os.path.exists(args.test_file):
            rag_system.create_submission(args.test_file, args.output_file)
        else:
            print(f"Test file not found: {args.test_file}")
