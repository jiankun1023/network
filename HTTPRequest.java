import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

final class HTTPRequest {
    enum Command {
        GET,
        HEAD,
        POST,
        UNK,
    };

    private Command command;
    private final String version;
    private final String path;
    private final Map<String, String> headers;

    public HTTPRequest(List<String> rawLines) {
        assert(rawLines.size() > 0); // requires at least the request; headers are optional.

        // Parse the main request (first line) first.
        String[] bits = rawLines.get(0).split(" ");
        assert(bits.length == 3);
        try {
            this.command = Command.valueOf(bits[0]);
        } catch (IllegalArgumentException e) {
            System.out.println("Illegal HTTP op code received [" + bits[0] + "]");
            this.command = Command.UNK;
        }
        this.path = bits[1];
        this.version = bits[2];

        // Then, parse any headers that are present
        this.headers = new HashMap<String, String>();
        for (String headerLine : rawLines.subList(1, rawLines.size())) {
            // Can't just split on ":" because the colon may appear in a value, too.
            int splitIdx = headerLine.indexOf(':');
            if ((splitIdx < 1) || (splitIdx >= headerLine.length() - 2)) {
                if (!headerLine.isEmpty()) {
                    System.out.println(String.format("malformed header: [%s]", headerLine));
                }
            } else {
                String key = headerLine.substring(0, splitIdx);
                String value = headerLine.substring(splitIdx + 2, headerLine.length());
                headers.put(key, value);
            }
        }
    }

    public Command getType() {
        return command;
    }

    public String getPath() {
        return path;
    }

    @Override
    public String toString() {
        StringBuilder out = new StringBuilder();
        out.append(String.format("HTTP request, version [%s]\n", version));
        out.append(String.format("%s [%s]\n", command, path));
        out.append("Headers:\n");
        for (Map.Entry<String, String> header : headers.entrySet()) {
            out.append(String.format("\t[%s] --> [%s]\n", header.getKey(), header.getValue()));
        }
        return out.toString();
    }
}
