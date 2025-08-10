# -*- coding: utf-8 -*-
"""
图像预处理器 - 优化OCR识别效果
基于OpenCV的专业图像处理管道
"""
import os
import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import io

# OpenCV导入
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False

# PIL导入
try:
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    Image = None
    ImageEnhance = None  
    ImageFilter = None
    HAS_PIL = False

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    图像预处理器
    - 图像质量检测和增强
    - 倾斜校正
    - 噪声去除
    - OCR优化预处理
    """
    
    def __init__(self):
        self.has_opencv = HAS_OPENCV
        self.has_pil = HAS_PIL
        
        # 预处理参数配置
        self.config = {
            "target_dpi": 300,          # 目标DPI
            "min_contour_area": 100,    # 最小轮廓面积
            "blur_kernel_size": 3,      # 模糊核大小
            "morph_kernel_size": 2,     # 形态学操作核大小
            "skew_angle_threshold": 0.5, # 倾斜角度阈值（度）
            "noise_reduction_strength": 1.0  # 降噪强度
        }
        
        if not self.has_opencv:
            logger.warning("OpenCV未安装，图像预处理功能将受限")
        if not self.has_pil:
            logger.warning("PIL未安装，基础图像处理不可用")
    
    def analyze_image_quality(self, image_data: bytes, enable_smart_preprocessing: bool = True) -> Dict[str, Any]:
        """
        分析图像质量
        确定需要哪些预处理步骤
        
        Args:
            image_data: 图像数据
            enable_smart_preprocessing: 是否启用智能预处理优化（默认True）
        """
        analysis = {
            "width": 0,
            "height": 0,
            "channels": 0,
            "estimated_dpi": 0,
            "is_skewed": False,
            "skew_angle": 0.0,
            "has_noise": False,
            "contrast_level": "unknown",  # low, medium, high
            "brightness_level": "unknown", # dark, normal, bright
            "needs_preprocessing": False,
            "recommended_steps": [],
            "processing_difficulty": "easy"  # easy, medium, hard
        }
        
        if not self.has_opencv or not self.has_pil:
            analysis["error"] = "缺少图像处理库"
            return analysis
        
        try:
            # 使用PIL获取基本信息
            pil_image = Image.open(io.BytesIO(image_data))
            analysis["width"] = pil_image.width
            analysis["height"] = pil_image.height
            analysis["channels"] = len(pil_image.getbands())
            
            # 估算DPI
            if hasattr(pil_image, 'info') and 'dpi' in pil_image.info:
                analysis["estimated_dpi"] = pil_image.info['dpi'][0]
            else:
                # 根据图像尺寸估算DPI
                pixel_count = analysis["width"] * analysis["height"]
                if pixel_count < 500000:  # < 0.5MP
                    analysis["estimated_dpi"] = 150
                elif pixel_count < 2000000:  # < 2MP
                    analysis["estimated_dpi"] = 200
                else:
                    analysis["estimated_dpi"] = 300
            
            # 转换为OpenCV格式进行详细分析
            cv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            if cv_image is None:
                analysis["error"] = "图像格式不支持"
                return analysis
            
            # 转换为灰度图像进行分析
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY) if len(cv_image.shape) == 3 else cv_image
            
            # 检测倾斜角度
            skew_angle = self._detect_skew_angle(gray)
            analysis["skew_angle"] = skew_angle
            analysis["is_skewed"] = abs(skew_angle) > self.config["skew_angle_threshold"]
            
            # 检测噪声水平
            noise_level = self._detect_noise_level(gray)
            analysis["has_noise"] = noise_level > 0.3
            
            # 分析对比度
            contrast_score = self._analyze_contrast(gray)
            if contrast_score < 30:
                analysis["contrast_level"] = "low"
            elif contrast_score > 80:
                analysis["contrast_level"] = "high"
            else:
                analysis["contrast_level"] = "medium"
            
            # 分析亮度
            mean_brightness = np.mean(gray)
            if mean_brightness < 80:
                analysis["brightness_level"] = "dark"
            elif mean_brightness > 180:
                analysis["brightness_level"] = "bright"
            else:
                analysis["brightness_level"] = "normal"
            
            # 确定推荐的预处理步骤
            recommended_steps = []
            
            if enable_smart_preprocessing:
                # 智能预处理：只对真正需要的图像进行处理
                quality_issues = 0
                
                if analysis["estimated_dpi"] < 200:  # 提高DPI阈值
                    recommended_steps.append("upscale")
                    quality_issues += 1
                
                if analysis["is_skewed"]:
                    recommended_steps.append("deskew")
                    quality_issues += 2  # 倾斜问题权重更高
                
                if analysis["has_noise"] and analysis["contrast_level"] == "low":
                    # 只有在对比度低且有噪点时才去噪
                    recommended_steps.append("denoise")
                    quality_issues += 1
                
                if analysis["contrast_level"] == "low":
                    recommended_steps.append("enhance_contrast")
                    quality_issues += 1
                
                if analysis["brightness_level"] in ["dark", "bright"]:
                    recommended_steps.append("adjust_brightness")
                    quality_issues += 1
                
                # 智能二值化：只对低质量图像进行二值化
                if quality_issues >= 2 or analysis["contrast_level"] == "low":
                    recommended_steps.append("binarize")
                
                analysis["needs_preprocessing"] = quality_issues >= 2  # 至少2个质量问题才预处理
            else:
                # 传统模式：保持原有逻辑
                if analysis["estimated_dpi"] < 250:
                    recommended_steps.append("upscale")
                
                if analysis["is_skewed"]:
                    recommended_steps.append("deskew")
                
                if analysis["has_noise"]:
                    recommended_steps.append("denoise")
                
                if analysis["contrast_level"] == "low":
                    recommended_steps.append("enhance_contrast")
                
                if analysis["brightness_level"] in ["dark", "bright"]:
                    recommended_steps.append("adjust_brightness")
                
                recommended_steps.append("binarize")
                analysis["needs_preprocessing"] = len(recommended_steps) > 1
            
            analysis["recommended_steps"] = recommended_steps
            
            # 评估处理难度
            difficulty_score = len(recommended_steps)
            if analysis["is_skewed"]:
                difficulty_score += 1
            if analysis["has_noise"]:
                difficulty_score += 1
            
            if difficulty_score <= 2:
                analysis["processing_difficulty"] = "easy"
            elif difficulty_score <= 4:
                analysis["processing_difficulty"] = "medium"
            else:
                analysis["processing_difficulty"] = "hard"
            
        except Exception as e:
            analysis["error"] = f"图像分析失败: {str(e)}"
            logger.error(f"图像质量分析失败: {e}")
        
        return analysis
    
    def preprocess_for_ocr(self, image_data: bytes, analysis: Optional[Dict] = None, enable_smart_preprocessing: bool = True) -> Tuple[Optional[bytes], Optional[str]]:
        """
        为OCR优化预处理图像
        
        Args:
            image_data: 原始图像数据
            analysis: 图像质量分析结果（可选）
            enable_smart_preprocessing: 是否启用智能预处理（默认True）
            
        Returns:
            Tuple[processed_image_data, error]: (处理后的图像数据, 错误信息)
        """
        if not self.has_opencv or not self.has_pil:
            return None, "缺少图像处理库 (OpenCV, PIL)"
        
        try:
            # 如果没有提供分析结果，先进行分析
            if analysis is None:
                analysis = self.analyze_image_quality(image_data, enable_smart_preprocessing)
                if "error" in analysis:
                    return None, analysis["error"]
            
            logger.info(f"开始图像预处理，难度: {analysis.get('processing_difficulty', 'unknown')}")
            logger.info(f"预处理步骤: {analysis.get('recommended_steps', [])}")
            
            # 解码图像
            cv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            if cv_image is None:
                return None, "无法解码图像"
            
            # 转换为灰度图（如果需要）
            if len(cv_image.shape) == 3:
                processed_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            else:
                processed_image = cv_image.copy()
            
            # 按推荐步骤进行处理
            for step in analysis.get("recommended_steps", []):
                try:
                    if step == "upscale":
                        processed_image = self._upscale_image(processed_image, target_dpi=self.config["target_dpi"])
                    elif step == "deskew":
                        processed_image = self._deskew_image(processed_image, analysis["skew_angle"])
                    elif step == "denoise":
                        processed_image = self._denoise_image(processed_image)
                    elif step == "enhance_contrast":
                        processed_image = self._enhance_contrast(processed_image)
                    elif step == "adjust_brightness":
                        processed_image = self._adjust_brightness(processed_image, analysis["brightness_level"])
                    elif step == "binarize":
                        processed_image = self._binarize_image(processed_image)
                    
                    logger.debug(f"完成预处理步骤: {step}")
                    
                except Exception as e:
                    logger.warning(f"预处理步骤失败 {step}: {e}")
                    continue
            
            # 编码处理后的图像
            success, encoded_image = cv2.imencode('.png', processed_image)
            if not success:
                return None, "图像编码失败"
            
            processed_data = encoded_image.tobytes()
            
            logger.info(f"图像预处理完成，原始大小: {len(image_data)}, 处理后大小: {len(processed_data)}")
            
            return processed_data, None
            
        except Exception as e:
            error_msg = f"图像预处理失败: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _detect_skew_angle(self, gray_image: np.ndarray) -> float:
        """
        检测图像倾斜角度
        使用霍夫变换检测直线
        """
        try:
            # 边缘检测
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # 霍夫变换检测直线
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None or len(lines) == 0:
                return 0.0
            
            # 计算主要角度
            angles = []
            for rho, theta in lines[:min(20, len(lines))]:  # 最多使用20条线
                angle = theta * 180 / np.pi
                # 转换为倾斜角度（-90到90度）
                if angle > 90:
                    angle = angle - 180
                angles.append(angle)
            
            # 返回中位数角度
            return float(np.median(angles))
            
        except Exception as e:
            logger.debug(f"倾斜角度检测失败: {e}")
            return 0.0
    
    def _detect_noise_level(self, gray_image: np.ndarray) -> float:
        """
        检测噪声水平
        使用拉普拉斯算子检测变化程度
        """
        try:
            # 计算拉普拉斯变换
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            
            # 计算方差作为噪声指标
            variance = laplacian.var()
            
            # 归一化到0-1范围
            noise_level = min(variance / 1000, 1.0)  # 经验值
            
            return float(noise_level)
            
        except Exception:
            return 0.0
    
    def _analyze_contrast(self, gray_image: np.ndarray) -> float:
        """
        分析图像对比度
        """
        try:
            # 计算标准差作为对比度指标
            contrast = gray_image.std()
            return float(contrast)
            
        except Exception:
            return 50.0  # 默认中等对比度
    
    def _upscale_image(self, image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
        """
        放大图像到目标DPI
        """
        try:
            height, width = image.shape[:2]
            
            # 简单的2倍放大（可以根据需要调整）
            scale_factor = 2.0
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # 使用高质量的双三次插值
            upscaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return upscaled
            
        except Exception as e:
            logger.warning(f"图像放大失败: {e}")
            return image
    
    def _deskew_image(self, image: np.ndarray, skew_angle: float) -> np.ndarray:
        """
        校正图像倾斜
        """
        try:
            if abs(skew_angle) < 0.1:  # 角度太小，不需要校正
                return image
            
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            
            # 创建旋转矩阵
            rotation_matrix = cv2.getRotationMatrix2D(center, -skew_angle, 1.0)
            
            # 应用旋转
            deskewed = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                    flags=cv2.INTER_LINEAR, 
                                    borderMode=cv2.BORDER_REPLICATE)
            
            return deskewed
            
        except Exception as e:
            logger.warning(f"倾斜校正失败: {e}")
            return image
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像降噪
        """
        try:
            # 双边滤波 - 保持边缘的同时降噪
            denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
            
            # 可选：形态学操作进一步清理
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                             (self.config["morph_kernel_size"], 
                                              self.config["morph_kernel_size"]))
            denoised = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
            
            return denoised
            
        except Exception as e:
            logger.warning(f"图像降噪失败: {e}")
            return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        增强对比度
        """
        try:
            # CLAHE (对比度限制自适应直方图均衡化)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"对比度增强失败: {e}")
            return image
    
    def _adjust_brightness(self, image: np.ndarray, brightness_level: str) -> np.ndarray:
        """
        调整亮度
        """
        try:
            if brightness_level == "dark":
                # 增亮
                adjusted = cv2.convertScaleAbs(image, alpha=1.2, beta=30)
            elif brightness_level == "bright":  
                # 减暗
                adjusted = cv2.convertScaleAbs(image, alpha=0.8, beta=-20)
            else:
                return image  # 正常亮度不调整
            
            return adjusted
            
        except Exception as e:
            logger.warning(f"亮度调整失败: {e}")
            return image
    
    def _binarize_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像二值化
        使用自适应阈值获得最佳效果
        """
        try:
            # 方法1: 自适应阈值
            binary1 = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
            
            # 方法2: Otsu自动阈值
            _, binary2 = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 选择更好的结果（基于文本区域的连通性）
            contours1, _ = cv2.findContours(binary1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours2, _ = cv2.findContours(binary2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 计算合适大小的连通区域数量
            good_contours1 = sum(1 for c in contours1 if cv2.contourArea(c) > self.config["min_contour_area"])
            good_contours2 = sum(1 for c in contours2 if cv2.contourArea(c) > self.config["min_contour_area"])
            
            # 选择连通区域更多的结果（通常文本更清晰）
            if good_contours1 >= good_contours2:
                return binary1
            else:
                return binary2
                
        except Exception as e:
            logger.warning(f"图像二值化失败: {e}")
            # 简单阈值作为备用
            try:
                _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
                return binary
            except:
                return image
    
    def create_processing_pipeline(self, steps: List[str]) -> callable:
        """
        创建自定义处理管道
        """
        def pipeline(image_data: bytes) -> Tuple[Optional[bytes], Optional[str]]:
            try:
                cv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_GRAYSCALE)
                if cv_image is None:
                    return None, "无法解码图像"
                
                processed = cv_image.copy()
                
                for step in steps:
                    if hasattr(self, f"_{step}"):
                        method = getattr(self, f"_{step}")
                        processed = method(processed)
                    else:
                        logger.warning(f"未知的处理步骤: {step}")
                
                success, encoded = cv2.imencode('.png', processed)
                if success:
                    return encoded.tobytes(), None
                else:
                    return None, "图像编码失败"
                    
            except Exception as e:
                return None, f"处理管道执行失败: {str(e)}"
        
        return pipeline
    
    def get_optimal_preprocessing_config(self, document_type: str = "general") -> Dict[str, Any]:
        """
        获取针对特定文档类型的最优预处理配置
        """
        configs = {
            "general": {
                "target_dpi": 300,
                "enhance_contrast": True,
                "denoise": True,
                "deskew": True,
                "binarize": True
            },
            "chinese": {
                "target_dpi": 400,  # 中文需要更高分辨率
                "enhance_contrast": True,
                "denoise": True,
                "deskew": True,
                "binarize": True,
                "morph_kernel_size": 1  # 更小的核，保持汉字结构
            },
            "printed": {
                "target_dpi": 300,
                "enhance_contrast": False,  # 印刷品通常对比度较好
                "denoise": False,
                "deskew": True,
                "binarize": True
            },
            "handwritten": {
                "target_dpi": 400,
                "enhance_contrast": True,
                "denoise": True,
                "deskew": True,
                "binarize": False,  # 手写字体可能需要灰度信息
                "blur_reduction": True
            }
        }
        
        return configs.get(document_type, configs["general"])