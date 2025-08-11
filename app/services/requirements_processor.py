import pandas as pd
import os
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog
from app.config.settings import settings

logger = structlog.get_logger()


class RequirementsFileProcessor:
    """Processador de arquivos de requisitos (XLSX/CSV)"""
    
    def __init__(self):
        self.upload_dir = Path(settings.uploads_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.logger = logger.bind(service="requirements_processor")
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Salva arquivo carregado no diretório de uploads
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome original do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        try:
            # Gerar nome único para o arquivo
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # Salvar arquivo
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            self.logger.info(
                "File saved successfully",
                original_filename=filename,
                saved_path=str(file_path)
            )
            
            return str(file_path)
            
        except Exception as e:
            self.logger.error("Error saving uploaded file", error=str(e))
            raise
    
    async def process_requirements_file(self, file_path: str) -> Dict[str, Any]:
        """
        Processa arquivo de requisitos e extrai informações estruturadas
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            Dicionário com dados estruturados dos requisitos
        """
        try:
            self.logger.info("Processing requirements file", file_path=file_path)
            
            # Determinar tipo de arquivo
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Processar dados
            requirements_data = await self._extract_requirements_data(df)
            
            self.logger.info(
                "Requirements file processed successfully",
                total_requirements=len(requirements_data.get('requirements', []))
            )
            
            return requirements_data
            
        except Exception as e:
            self.logger.error("Error processing requirements file", error=str(e))
            raise
    
    async def _extract_requirements_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extrai dados estruturados do DataFrame
        
        Args:
            df: DataFrame com dados do arquivo
            
        Returns:
            Dicionário com requisitos estruturados
        """
        try:
            # Detectar colunas automaticamente baseado em padrões comuns
            column_mapping = self._detect_columns(df)
            
            requirements = []
            
            for index, row in df.iterrows():
                try:
                    # Extrair dados básicos do requisito
                    requirement = {
                        "id": self._extract_value(row, column_mapping.get('id'), f"REQ-{index+1:03d}"),
                        "description": self._extract_value(row, column_mapping.get('description'), ""),
                        "category": self._extract_value(row, column_mapping.get('category'), "Functional"),
                        "priority": self._extract_value(row, column_mapping.get('priority'), "Medium"),
                        "status": self._extract_value(row, column_mapping.get('status'), "New"),
                        "business_process": self._extract_value(row, column_mapping.get('business_process'), ""),
                        "acceptance_criteria": self._extract_value(row, column_mapping.get('acceptance_criteria'), ""),
                        "notes": self._extract_value(row, column_mapping.get('notes'), ""),
                        "source_row": index + 1
                    }
                    
                    # Adicionar campos específicos se detectados
                    if column_mapping.get('effort'):
                        requirement["effort_estimate"] = self._extract_value(row, column_mapping['effort'], "")
                    
                    if column_mapping.get('module'):
                        requirement["sap_module"] = self._extract_value(row, column_mapping['module'], "")
                    
                    if column_mapping.get('complexity'):
                        requirement["complexity"] = self._extract_value(row, column_mapping['complexity'], "")
                    
                    # Filtrar requisitos vazios
                    if requirement["description"].strip():
                        requirements.append(requirement)
                        
                except Exception as e:
                    self.logger.warning(
                        "Error processing requirement row",
                        row_number=index+1,
                        error=str(e)
                    )
                    continue
            
            # Extrair metadados do arquivo
            metadata = {
                "total_rows": len(df),
                "total_requirements": len(requirements),
                "columns_detected": list(column_mapping.keys()),
                "column_mapping": column_mapping
            }
            
            return {
                "requirements": requirements,
                "metadata": metadata,
                "raw_columns": list(df.columns)
            }
            
        except Exception as e:
            self.logger.error("Error extracting requirements data", error=str(e))
            raise
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detecta automaticamente as colunas baseado em padrões comuns
        
        Args:
            df: DataFrame a ser analisado
            
        Returns:
            Mapeamento de tipos de coluna para nomes de coluna
        """
        column_mapping = {}
        columns_lower = {col.lower(): col for col in df.columns}
        
        # Padrões para detecção de colunas
        patterns = {
            'id': ['id', 'key', 'código', 'codigo', 'identifier', 'req_id', 'requirement_id'],
            'description': ['description', 'descrição', 'descricao', 'requirement', 'requisito', 'desc'],
            'category': ['category', 'categoria', 'type', 'tipo', 'classification'],
            'priority': ['priority', 'prioridade', 'urgency', 'urgencia', 'importance'],
            'status': ['status', 'state', 'estado', 'situation', 'situacao'],
            'business_process': ['process', 'processo', 'business_process', 'bpmn', 'workflow'],
            'acceptance_criteria': ['criteria', 'criterio', 'acceptance', 'aceitacao', 'validation'],
            'notes': ['notes', 'notas', 'comments', 'comentarios', 'observations', 'observacoes'],
            'effort': ['effort', 'esforco', 'estimate', 'estimativa', 'hours', 'horas', 'days', 'dias'],
            'module': ['module', 'modulo', 'sap_module', 'area', 'domain'],
            'complexity': ['complexity', 'complexidade', 'difficulty', 'dificuldade']
        }
        
        # Detectar colunas baseado nos padrões
        for column_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in columns_lower:
                    column_mapping[column_type] = columns_lower[keyword]
                    break
        
        # Se não encontrou descrição, usar a primeira coluna com texto
        if 'description' not in column_mapping:
            for col in df.columns:
                if df[col].dtype == 'object' and not df[col].isna().all():
                    column_mapping['description'] = col
                    break
        
        return column_mapping
    
    def _extract_value(self, row: pd.Series, column: Optional[str], default: str = "") -> str:
        """
        Extrai valor de uma coluna da linha, com fallback para default
        
        Args:
            row: Linha do DataFrame
            column: Nome da coluna
            default: Valor padrão se coluna não existir ou estiver vazia
            
        Returns:
            Valor extraído ou default
        """
        if not column or column not in row:
            return default
        
        value = row[column]
        
        # Tratar valores NaN/None
        if pd.isna(value):
            return default
        
        # Converter para string e limpar
        return str(value).strip()
    
    def cleanup_file(self, file_path: str) -> None:
        """
        Remove arquivo temporário
        
        Args:
            file_path: Caminho do arquivo a ser removido
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info("Temporary file cleaned up", file_path=file_path)
        except Exception as e:
            self.logger.warning("Error cleaning up file", file_path=file_path, error=str(e))


# Instância global do processador
requirements_processor = RequirementsFileProcessor()
