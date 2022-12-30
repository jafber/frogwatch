module.exports = {
	globDirectory: 'build/',
	globPatterns: [
		'**/*.{html,css,json,png}'
	],
	swDest: 'build/sw.js',
	ignoreURLParametersMatching: [
		/^utm_/,
		/^fbclid$/
	]
};