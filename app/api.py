from flask import Flask, request, jsonify, Response
from argparse import Namespace

from .scraper import run_scraper

app = Flask(__name__)


@app.route('/packs', defaults={'action': None})
@app.route('/packs/<action>')
def get_packs(action):
    """
    Handles requests for packs.
    - /packs?format=json -> Lists all packs.
    - /packs/all?format=csv -> Scrapes all cards from all packs and saves them.
    """
    format_type = request.args.get('format', 'json')  # Default to json for API calls

    # Create a mock 'args' object to pass to the scraper logic
    args = Namespace(
        command='packs',
        action=action,
        format=format_type,
        verbose=True,
        debug=False
    )

    try:
        result = run_scraper(args)
        if action == 'all':
            # For 'packs all', the result is a confirmation message
            return jsonify({"status": "success", "message": result})
        else:
            # For a simple 'packs' list, return the formatted data
            if format_type == 'json':
                return jsonify(result)
            # For csv/text, return as plain text response
            return Response(result, mimetype='text/plain')
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/cards/<series_id>')
def get_cards(series_id):
    """
    Handles requests for cards from a specific series.
    - /cards/556101?format=json -> Lists all cards in pack OP-01.
    """
    format_type = request.args.get('format', 'json')

    args = Namespace(
        command='cards',
        series_id=series_id,
        format=format_type,
        verbose=True,
        debug=False
    )

    try:
        result = run_scraper(args)
        if format_type == 'json':
            return jsonify(result)
        return Response(result, mimetype='text/plain')
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
