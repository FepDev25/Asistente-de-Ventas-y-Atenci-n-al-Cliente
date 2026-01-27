1) Asistente de Gestión de Inventario (Agent + Planner)
Objetivo: registrar producto desde foto(s)
Plan (pipeline)
1.	Capture Agent
o	foto 1: frontal etiqueta
o	foto 2: tabla nutricional / código
o	foto 3: lote/fechas (si aplica)
2.	OCR + Vision Extractor Agent
o	OCR + parsing → campos normalizados
o	detecta: nombre, marca, presentación, peso/volumen, lote, exp/venc, precio base
3.	Normalizer Agent
o	unidades: g/kg/ml/l
o	fechas: ISO + sanity checks
o	nombre canónico + dedupe (similitud)
4.	DB Writer Agent
o	upsert producto + variantes + lotes
o	almacena imágenes (S3/minio) + metadata
5.	Verifier Agent
o	confidence threshold
o	si faltan campos críticos → pregunta puntual al usuario
Tools
	tool_ocr_extract(images[])
	tool_product_dedupe(name, brand, size)
	tool_inventory_upsert(payload)
	tool_store_images(images[])


2) Asistente de Reconocimiento de Productos (multiagente ML + planners)
Objetivo: clasificación multilabel + segmentación + servicio inferencia + training continuo
Agentes
	Data Agent
o	adquisición + versionado dataset (DVC/MinIO)
o	split train/val/test
	EDA/Prep Agent
o	stats, clases desbalanceadas
o	augmentations/transformaciones registradas
	Training Agent
o	fine-tuning (e.g., YOLO/Mask R-CNN/SegFormer según caso)
o	log con MLflow (params, metrics, artifacts)
	Registry/Deploy Agent
o	registra “Model Version” + stage (Staging/Prod)
o	empaqueta en servicio (FastAPI/Triton)
	Inference Agent
o	predicción: imagen / batch / video
o	salida: labels + masks + bboxes + confidence
	Continuous Learning Agent
o	selecciona “hard examples” (baja confianza) → cola de etiquetado
o	reentrena incremental y registra nueva versión
Plan (training)
1.	ingest → 2) EDA → 3) train → 4) evaluate → 5) register → 6) promote
Tools
	tool_mlflow_train(config, dataset_version)
	tool_mlflow_register(run_id, model_name)
	tool_mlflow_load(model_name, stage)
	tool_predict(image|video, model_ref)
	tool_active_learning_select(samples)
3) Asistente de Atención al Cliente (LLM Agent + RAG + Tools)
Objetivo: conversar + responder FAQ + consultar inventario + recomendar + registrar pedidos
Capas
	Router/Planner
o	clasifica: FAQ | RAG | Tool-call (inventario, reconocimiento, recomendación, pedido)
	RAG Agent
o	chunks: políticas, horarios, envíos, devoluciones, catálogo, promos
	Order Agent
o	crea pedido, valida stock, confirma dirección/pago
	Recommendation Agent
o	reglas + embeddings: “similaridad + disponibilidad + margen”
	Verifier Agent
o	evita alucinación: “si no hay en inventario, no inventar”
Tools (function calling)
	tool_product_recognition(image) → id(s) + confidence
	tool_inventory_query(filters) → stock, precio, caducidad, ubicación
	tool_recommend(products, user_profile, constraints)
	tool_order_create(cart, customer, delivery, payment)
Flujo tipo
1.	Usuario: “¿Tienen leche deslactosada?”
2.	Planner: tool → inventario
3.	Respuesta + opciones + upsell
4.	Si “sí, quiero 2” → tool_order_create
NOTAS:
–	Agentic  AI
–	Debemos pensar en el como, forma y herramientas de como encaminar hacerlo. Solucion clara y breve. Que tecnologias, usando las mejore tecnologias, dando la mejor solucion, pensando en agentic AI
