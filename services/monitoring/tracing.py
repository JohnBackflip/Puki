# monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def setup_tracing(app, service_name):
    # Set up the tracer
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer_provider()

    # Set up the OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer.add_span_processor(span_processor)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument requests
    RequestsInstrumentor().instrument()

    return tracer