from flask import Flask, render_template, request, jsonify
import os
import sys
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Phân tích review (Temporary version without AI)
    """
    try:
        review_text = request.json.get('review_text', '')
        
        if not review_text:
            return jsonify({'error': 'Vui lòng nhập nội dung review'}), 400
        
        # Temporary simple analysis without AI
        # Count words to simulate analysis
        word_count = len(review_text.split())
        
        if word_count < 10:
            sentiment = 'negative'
            confidence = 0.7
        elif word_count < 50:
            sentiment = 'neutral'  
            confidence = 0.6
        else:
            sentiment = 'positive'
            confidence = 0.8
            
        result = {
            'sentiment': sentiment,
            'confidence': confidence,
            'word_count': word_count,
            'message': 'Phân tích tạm thời (AI sẽ được thêm sau)'
        }
        
        logger.info(f"Analysis completed for review: {review_text[:50]}...")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze: {str(e)}")
        return jsonify({'error': 'Có lỗi xảy ra trong quá trình phân tích'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'message': 'App is running successfully!'})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Không tìm thấy trang'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Lỗi server nội bộ'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f"Starting app on port {port}, debug={debug}")
    app.run(debug=debug, host='0.0.0.0', port=port)